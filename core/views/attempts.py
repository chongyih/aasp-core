import time
import requests
from django.conf import settings

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Assessment, AssessmentAttempt, CodeQuestionAttempt, CodeQuestion, TestCase, CodeSnippet
from core.views.utils import get_assessment_attempt_question


@login_required()
def assessment_landing(request, assessment_id):
    """
    Landing page for a candidate taking an Assessment
    Displays the various information about an assessment
    """
    # get assessment object
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # check if user is enrolled into the course
    if not assessment.course.coursegroup_set.filter(students=request.user).exists():
        messages.warning(request, "You do not have permissions to view this assessment.")
        return redirect('dashboard')

    # check for incomplete attempts
    incomplete_attempt = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user, time_submitted=None).exists()

    # check if there are any attempts remaining
    attempt_count = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user).count()
    no_more_attempts = False if assessment.num_attempts == 0 else attempt_count >= assessment.num_attempts

    # context
    context = {
        'assessment': assessment,
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

        # check if user is enrolled into the course
        if not assessment.course.coursegroup_set.filter(students=request.user).exists():
            messages.warning(request, "You do not have permissions to view this assessment.")
            return redirect('dashboard')

        # check if assessment is active
        if assessment.status != "Active":
            messages.warning(request, "You may not enter this assessment.")
            return redirect('assessment-landing', assessment_id=assessment.id)

        # get incomplete attempt, if it exists
        incomplete_attempt = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user, time_submitted=None).first()
        if incomplete_attempt:
            return redirect('attempt-question', assessment_attempt_id=incomplete_attempt.id, question_index=0)

        # no incomplete attempt (create new one if permissible)
        attempt_count = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user).count()
        if assessment.num_attempts != 0 and attempt_count >= assessment.num_attempts:  # all attempts used up
            messages.warning(request, "You may not enter this assessment.")
            return redirect('assessment-landing', assessment_id=assessment.id)
        else:
            # generate new assessment_attempt
            generate_assessment_attempt(request.user, assessment)
            print("generated, sleeping now")
            time.sleep(5)
            print("sleep finished! redirecting.")
            return redirect('attempt-question', assessment_attempt_id=assessment.id, question_index=0)

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


def attempt_question(request, assessment_attempt_id, question_index):
    print("assessment_attempt_id:", assessment_attempt_id)
    print("question_index:", question_index)

    # get assessment attempt
    assessment_attempt = get_object_or_404(AssessmentAttempt, id=assessment_attempt_id)

    # get question
    question_count, question_attempt = get_assessment_attempt_question(assessment_attempt_id, question_index)

    # context
    context = {
        'assessment_attempt': assessment_attempt,
        'question_attempt': question_attempt,
        'question_index': question_index,
        'prev_index': question_index - 1 if question_index - 1 >= 0 else -1,
        'next_index': question_index + 1 if question_index + 1 < question_count else -1,
        'question_counts': range(question_count),
    }

    # render different template depending on question type (currently only CodeQuestion)
    if isinstance(question_attempt, CodeQuestionAttempt):
        print("CodeQuestion detected!")
        code_question = question_attempt.code_question
        code_snippets = CodeSnippet.objects.filter(code_question=code_question)
        sample_tc = TestCase.objects.filter(code_question=code_question, sample=True).first()
        print(code_snippets)
        # add to base context
        context.update({
            'code_question': code_question,
            'sample_tc': sample_tc,
            'code_snippets': code_snippets,
        })
        return render(request, "attempts/code-question-attempt.html", context)
    else:
        raise Exception("Unknown question!")


def submit_sample(request, test_case_id):
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
            "cpu_time_limit": 15, #test_case.time_limit / 1000,
            "memory_limit": 20480, #test_case.memory_limit,
        }

        # call judge0
        url = settings.JUDGE0_URL + "/submissions/?base64_encoded=false&wait=false"
        res = requests.post(url, json=params)
        data = res.json()

        # return error if no token
        token = data.get("token")
        if not token:
            print(data)
            return JsonResponse({"result": "error", "msg": "Judge0 error."})

        return JsonResponse({"result": "success", "token": token})


def get_sample_status(request):
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
        # get token from request
        token = request.GET.get('token')
        if not token:
            return JsonResponse({"result": "error"})

        # call judge0
        try:
            url = f"{settings.JUDGE0_URL}/submissions/{token}?base64_encoded=false&fields=status_id"
            res = requests.get(url)
            data = res.json()
            data['status'] = STATUSES[int(data['status_id'])]
        except ConnectionError:
            return JsonResponse({"result": "error", "msg": "API seems to be down."})

        return JsonResponse({"result": "success", "data": data})
