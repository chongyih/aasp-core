from datetime import timedelta

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import Assessment, AssessmentAttempt, CodeQuestionAttempt, CodeQuestion, TestCase, CodeSnippet, CodeQuestionSubmission, \
    TestCaseAttempt, Language
from core.tasks import update_test_case_attempt_status, update_cqs_passed_flag, force_submit_assessment, compute_assessment_attempt_score
from core.views.utils import get_assessment_attempt_question, check_permissions


@login_required()
def assessment_landing(request, assessment_id):
    """
    Landing page for a candidate taking an Assessment
    Displays the various information about an assessment
    """
    # get assessment object
    assessment = get_object_or_404(Assessment, id=assessment_id)

    if not assessment.published:  # not published: preview-only for educators
        # must be course owner or maintainer
        if check_permissions(assessment.course, request.user) == 0:
            messages.warning(request, "You do not have permissions to view this assessment.")
            return redirect('dashboard')

        # check if assessment is valid for previewing
        valid, msg = assessment.is_valid()

        if not valid:
            messages.warning(request, f"Assessment is incomplete! {msg}")
            return redirect("assessment-details", assessment_id=assessment_id)

    else:  # published: only for students
        # check if user is enrolled into the course (students)
        if not assessment.course.coursegroup_set.filter(students=request.user).exists():
            messages.warning(request, "You do not have permissions to view this assessment.")
            return redirect('dashboard')

    # check for incomplete attempts
    incomplete_attempt: bool = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user, time_submitted=None).exists()

    # check if there are any attempts remaining
    attempt_count: int = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user).count()
    no_more_attempts: bool = False if assessment.num_attempts == 0 else attempt_count >= assessment.num_attempts

    # get all existing assessment attempts
    assessment_attempts = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user)

    # context
    context = {
        'assessment': assessment,
        'assessment_attempts': assessment_attempts,
        'attempt_count': attempt_count,
        'incomplete_attempt': incomplete_attempt,
        'no_more_attempts': no_more_attempts,
    }

    return render(request, 'attempts/assessment-landing.html', context)


@login_required()
def enter_assessment(request, assessment_id):
    """
    This view will redirect the user to the assessment. POST method is selected to prevent CSRF attacks.
    If an incomplete AssessmentAttempt exists:
     - redirect to first question of this attempt
    If an AssessmentAttempt does not exist:
     - use generateAttempt() to generate models
     - redirect to first question of this attempt
    """
    if request.method == "POST":
        # get assessment object
        assessment = get_object_or_404(Assessment, id=assessment_id)
        pin = request.POST.get('pin')

        if not assessment.published:  # not published: preview-only for educators
            if check_permissions(assessment.course, request.user) == 0:
                messages.warning(request, "You do not have permissions to view this assessment.")
                return redirect('dashboard')
        else:  # published: only for students
            # check if user is enrolled into the course (students)
            if not assessment.course.coursegroup_set.filter(students=request.user).exists():
                messages.warning(request, "You do not have permissions to view this assessment.")
                return redirect('dashboard')

            # check if assessment is active (only needed for students)
            if assessment.status != "Active":
                messages.warning(request, "You may not enter this assessment.")
                return redirect('assessment-landing', assessment_id=assessment.id)

        # get incomplete attempt, if it exists
        incomplete_attempt = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user, time_submitted=None).first()
        if incomplete_attempt:
            print("incomplete attempt exist")
            return redirect('attempt-question', assessment_attempt_id=incomplete_attempt.id, question_index=0)

        # no incomplete attempt (create new one if permissible)
        attempt_count = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user).count()
        if assessment.num_attempts != 0 and attempt_count >= assessment.num_attempts:  # all attempts used up
            messages.warning(request, "You may not enter this assessment.")
            return redirect('assessment-landing', assessment_id=assessment.id)
        else:
            # check pin, if needed
            if assessment.pin is not None and str(assessment.pin) != pin:
                messages.warning(request, "Incorrect PIN supplied, unable to start a new attempt.")
                return redirect('assessment-landing', assessment_id=assessment.id)

            # generate new assessment_attempt
            assessment_attempt = generate_assessment_attempt(request.user, assessment)
            return redirect('attempt-question', assessment_attempt_id=assessment_attempt.id, question_index=0)

    raise Http404


def generate_assessment_attempt(user, assessment):
    """
    Generates a AssessmentAttempt instance for a user and assessment then,
    generates a cq_attempt instance for each CodeQuestion added to this assessment.
    (If there are other types of questions in the future, they should be generated here as well)
    """
    with transaction.atomic():
        # create assessment attempt object
        assessment_attempt = AssessmentAttempt.objects.create(candidate=user, assessment=assessment)

        # generate a cq_attempt for each code question in the assessment
        code_questions = CodeQuestion.objects.filter(assessment=assessment).order_by('id')
        cq_attempts = [CodeQuestionAttempt(assessment_attempt=assessment_attempt, code_question=cq) for cq in code_questions]
        CodeQuestionAttempt.objects.bulk_create(cq_attempts)

    # queue celery auto submit
    duration = assessment_attempt.assessment.duration
    if duration != 0:
        auto_submission_time = timezone.now() + timedelta(minutes=duration)
        force_submit_assessment.apply_async((assessment_attempt.id,), eta=auto_submission_time)

    return assessment_attempt


@login_required()
def attempt_question(request, assessment_attempt_id, question_index):
    # get assessment attempt
    assessment_attempt = get_object_or_404(AssessmentAttempt, id=assessment_attempt_id)

    # disallow if assessment already submitted
    if assessment_attempt.time_submitted:
        raise PermissionDenied

    # get question
    question_statuses, question_attempt = get_assessment_attempt_question(assessment_attempt_id, question_index)

    # if no question exist at the index, raise 404
    if not question_attempt:
        raise Http404

    # context
    context = {
        'question_index': question_index,
        'assessment_attempt': assessment_attempt,
        'question_attempt': question_attempt,
        'question_statuses': question_statuses,
    }

    # render different template depending on question type (currently only CodeQuestion)
    if isinstance(question_attempt, CodeQuestionAttempt):
        code_question = question_attempt.code_question
        code_snippets = CodeSnippet.objects.filter(code_question=code_question)
        sample_tc = TestCase.objects.filter(code_question=code_question, sample=True).first()
        code_question_submissions = CodeQuestionSubmission.objects.filter(cq_attempt=question_attempt).order_by('-id')
        # add to base context
        context.update({
            'code_question': code_question,
            'sample_tc': sample_tc,
            'code_snippets': code_snippets,
            'code_question_submissions': code_question_submissions,
        })
        return render(request, "attempts/code-question-attempt.html", context)
    else:
        raise Exception("Unknown question!")


@login_required()
def submit_single_test_case(request, test_case_id):
    """
    Submits a single test case to judge0 for execution, returns the token.
    This is used for the "Compile and Run" option for users to run the sample test case.
    This submission is not recorded.
    """
    if request.method == "POST":
        # get test case instance
        test_case = TestCase.objects.filter(id=test_case_id).first()
        if not test_case:
            return JsonResponse({"result": "error", "msg": "The specified Test Case does not exist."})

        # judge0 params
        params = {
            "source_code": request.POST.get('code'),
            "language_id": request.POST.get('lang-id'),
            "stdin": test_case.stdin,
            "expected_output": test_case.stdout,
            "cpu_time_limit": test_case.time_limit,
            "memory_limit": test_case.memory_limit,
        }

        # call judge0
        try:
            url = settings.JUDGE0_URL + "/submissions/?base64_encoded=false&wait=false"
            res = requests.post(url, json=params)
            data = res.json()
        except requests.exceptions.ConnectionError:
            return JsonResponse({"result": "error", "msg": "Judge0 API seems to be down."})

        # return error if no token
        token = data.get("token")
        if not token:
            print(data)
            return JsonResponse({"result": "error", "msg": "Judge0 error."})

        return JsonResponse({"result": "success", "token": token})


@login_required()
def get_tc_details(request):
    """
    Retrieves the status_id of a submission from Judge0, given a token.
    Used for checking the status of a submitted sample test case.
    """
    # friendly names of status_ids
    STATUSES = {
        1: "In Queue",
        2: "Processing",
        3: "Accepted",
        4: "Wrong Answer",
        5: "Time Limit Exceeded",
        6: "Compilation Error",
        7: "Runtime Error SIGSEGV",
        8: "Runtime Error SIGXFSZ",
        9: "Runtime Error SIGFPE",
        10: "Runtime Error SIGABRT",
        11: "Runtime Error NZEC",
        12: "Runtime Error Other",
        13: "Internal Error",
        14: "Exec Format Error",
    }

    if request.method == "GET":
        # get parameters from request
        status_only = request.GET.get('status_only') == 'true'
        token = request.GET.get('token')
        if not token:
            return JsonResponse({"result": "error"})

        # call judge0
        try:
            if status_only:
                url = f"{settings.JUDGE0_URL}/submissions/{token}?base64_encoded=false&fields=status_id"
            else:
                url = f"{settings.JUDGE0_URL}/submissions/{token}?base64_encoded=false&fields=status_id,stdin,stdout,expected_output"

            res = requests.get(url)
            data = res.json()

            # append friendly status name
            data['status'] = STATUSES[int(data['status_id'])]

            # hide fields if this belongs to a hidden test case
            if TestCase.objects.filter(hidden=True, testcaseattempt__token=token).exists():
                data['stdin'] = "Hidden"
                data['stdout'] = "Hidden"
                data['expected_output'] = "Hidden"

            return JsonResponse({"result": "success", "data": data})

        except requests.exceptions.ConnectionError:
            return JsonResponse({"result": "error", "msg": "Judge0 API seems to be down."})


@login_required()
def code_question_submission(request, code_question_attempt_id):
    """
    Submits answer for a code question.
    - Generates 'CodeQuestionSubmission' and 'TestCaseAttempt's and stores in the database.
    - Calls Judge0 api for the submission of the test cases
    - Queues celery tasks for updating the statuses of TestCaseAttempt
    """

    if request.method == "POST":
        # get cqa object
        cqa = CodeQuestionAttempt.objects.filter(id=code_question_attempt_id).first()
        if not cqa:
            return JsonResponse({"result": "error", "msg": "CQA does not exist."})

        # cqa does not belong to the request user
        if cqa.assessment_attempt.candidate != request.user:
            return JsonResponse({"result": "error", "msg": "You do not have permissions to perform this action."})

        # get test cases
        test_cases = TestCase.objects.filter(code_question__codequestionattempt=cqa)

        # generate params for judge0 call
        code = request.POST.get('code')
        language_id = request.POST.get('lang-id')
        submissions = [{
            "source_code": code,
            "language_id": language_id,
            "stdin": test_case.stdin,
            "expected_output": test_case.stdout,
            "cpu_time_limit": test_case.time_limit,
            "memory_limit": test_case.memory_limit,
        } for test_case in test_cases]
        params = {"submissions": submissions}

        # call judge0
        try:
            url = settings.JUDGE0_URL + "/submissions/batch?base64_encoded=false"
            res = requests.post(url, json=params)
            data = res.json()
        except ConnectionError:
            return JsonResponse({"result": "error", "msg": "Judge0 API seems to be down."})

        # retrieve tokens from judge0 response
        tokens = [x['token'] for x in data]

        with transaction.atomic():
            # create CodeQuestionSubmission
            cqs = CodeQuestionSubmission.objects.create(cq_attempt=cqa, code=code, language=Language.objects.get(judge_language_id=language_id))

            # create TestCaseAttempts
            test_case_attempts = TestCaseAttempt.objects.bulk_create([
                TestCaseAttempt(cq_submission=cqs, test_case=tc, token=token) for tc, token in zip(test_cases, tokens)
            ])

        # queue celery tasks
        for tca in test_case_attempts:
            update_test_case_attempt_status.delay(tca.id, tca.token, 1)

        context = {
            "result": "success",
            "cqs_id": cqs.id,
            "time_submitted": timezone.localtime(cqs.time_submitted).strftime("%d/%m/%Y %I:%M %p"),
            "statuses": [[tca.id, tca.status, tca.token] for tca in test_case_attempts]
        }
        return JsonResponse(context)


@login_required()
def get_cq_submission_status(request):
    """
    Returns the statuses of each TestCaseAttempt belonging to a CodeQuestionSubmission.
    """
    if request.method == "GET":
        cq_submission_id = request.GET.get("cqs_id")

        # get test case attempts
        statuses = list(TestCaseAttempt.objects.filter(cq_submission=cq_submission_id).values_list('id', 'status', 'token'))
        cqs = CodeQuestionSubmission.objects.get(id=cq_submission_id)

        context = {
            "result": "success",
            "cqs_id": cq_submission_id,
            "outcome": cqs.outcome,
            "statuses": statuses
        }
        return JsonResponse(context)


@login_required()
def submit_assessment(request, assessment_attempt_id):
    if request.method == "POST":
        # check permissions
        assessment_attempt = get_object_or_404(AssessmentAttempt, id=assessment_attempt_id)
        if assessment_attempt.candidate != request.user:
            messages.warning(request, "You do not have permissions to perform this action.")
            return redirect('dashboard')

        # set time_submitted
        if assessment_attempt.time_submitted is None:
            assessment_attempt.auto_submit = False
            assessment_attempt.time_submitted = timezone.now()
            assessment_attempt.save()
            compute_assessment_attempt_score.delay(assessment_attempt.id)
            messages.success(request, "Assessment submitted successfully!")
        else:
            messages.warning(request, "Assessment was already submitted previously.")

        return redirect('assessment-landing', assessment_id=assessment_attempt.assessment.id)
