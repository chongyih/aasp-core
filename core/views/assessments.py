from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from core.filters import CodeQuestionFilter
from core.forms.assessments import AssessmentForm
from core.models import Course, Assessment, CodeQuestion, TestCase, CodeSnippet, Tag, QuestionBank
from core.serializers import CodeQuestionsSerializer
from core.views.utils import check_permissions, check_permissions_assessment, check_permissions_code_question


@login_required()
def create_assessment(request):
    # get course_id if exists
    course_id = request.GET.get('course_id')

    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct().prefetch_related('owner', 'maintainers')

    # form
    form = AssessmentForm(courses=courses, initial={'course': course_id})

    # process POST request
    if request.method == "POST":
        form = AssessmentForm(courses, request.POST)

        if form.is_valid():
            # get course object
            course = get_object_or_404(Course, id=form.data['course'])

            # check permissions before saving form
            if check_permissions(course, request.user) == 0:
                messages.success(request, "You do not have permissions for this course.")
                return redirect('view-courses')

            assessment = form.save()

            # redirect
            messages.success(request, "The assessment has been successfully created! ✅")
            return redirect('assessment-details', assessment_id=assessment.id)

    context = {
        'form': form,
    }

    return render(request, 'assessments/create-assessment.html', context)


@login_required()
def assessment_details(request, assessment_id):
    # get assessment object
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # check permissions
    if check_permissions_assessment(assessment, request.user) == 0:
        messages.warning(request, "You do not have permissions to view this assessment.")
        return redirect('view-courses')

    # get all question banks accessible by this user
    all_question_banks = QuestionBank.objects.filter(
        Q(owner=request.user) | Q(shared_with=request.user, private=True) | Q(private=False)).distinct()

    # get all tags
    tags = Tag.objects.all()

    context = {
        'assessment': assessment,
        'all_question_banks': all_question_banks,
        'tags': tags,
    }

    return render(request, 'assessments/assessment-details.html', context)


@login_required()
def get_code_questions(request):
    # mytodo: add pagination for these
    if request.method == "GET":
        # get all question banks accessible by this user
        all_question_banks = QuestionBank.objects.filter(
            Q(owner=request.user) | Q(shared_with=request.user, private=True) | Q(private=False)).distinct()

        # get all code questions accessible by this user
        all_code_questions = CodeQuestion.objects.filter(question_bank__in=all_question_banks)
        code_question_filter = CodeQuestionFilter(all_question_banks, request.GET, queryset=all_code_questions)

        # serialize filtered queryset
        code_questions = CodeQuestionsSerializer(code_question_filter.qs, many=True)

        context = {
            "result": "success",
            "code_questions": code_questions.data,
        }

        return JsonResponse(context, status=200)

    return JsonResponse({"result": "error"}, status=200)


@login_required()
def add_code_question_to_assessment(request):
    if request.method == "POST":
        # default error response
        error_context = {"result": "error", }

        # get assessment object
        assessment = Assessment.objects.filter(id=request.POST.get('assessment_id')).first()
        if assessment is None:
            return JsonResponse(error_context, status=200)

        # check permissions
        if check_permissions_assessment(assessment, request.user) == 0:
            return JsonResponse(error_context, status=200)

        # get question
        code_question_id = request.POST.get('code_question_id')
        code_question = CodeQuestion.objects.filter(id=code_question_id).first()
        if code_question is None:
            return JsonResponse(error_context, status=200)

        tags = code_question.tags.all()

        # check permissions
        if check_permissions_code_question(code_question, request.user) is False:
            return JsonResponse(error_context, status=200)

        with transaction.atomic():
            # duplicate and link code question
            code_question.pk = None
            code_question.question_bank = None  # remove link to qb
            code_question.assessment = assessment  # link to current assessment
            code_question.save()

            # duplicate and link test cases
            test_cases = TestCase.objects.filter(code_question=code_question_id)
            for tc in test_cases:
                tc.pk = None
                tc.code_question = code_question
                tc.save()

            # duplicate and link code snippets
            code_snippets = CodeSnippet.objects.filter(code_question=code_question_id)
            for cs in code_snippets:
                cs.pk = None
                cs.code_question = code_question
                cs.save()

            # duplicate and link tags (M2M)
            for t in tags:
                code_question.tags.add(t.id)

        return JsonResponse({"result": "success"}, status=200)
