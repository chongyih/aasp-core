from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.forms.assessments import AssessmentForm
from core.models import Course, Assessment, CodeQuestion
from core.views.utils import check_permissions, check_permissions_assessment


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

            form.save()

            # redirect
            messages.success(request, "The assessment has been successfully created! ✅")
            return redirect('course-details', course_id=course.id)

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

    context = {
        'assessment': assessment,

    }

    return render(request, 'assessments/assessment-details.html', context)


@login_required()
def add_code_question_to_assessment(request):
    if request.method == "POST":
        # get assessment object
        assessment = Assessment.objects.filter(id=request.POST.assessment_id).first()

        # return if none
        if assessment is None:
            return JsonResponse({})

        # check permissions
        if check_permissions_assessment(assessment, request.user) == 0:
            return JsonResponse({})

        # get question id from POST
        code_question_id = request.POST.get('code_question_id')

        # get question
        code_question = CodeQuestion.objects.filter(id=code_question_id).first()

        # return if none
        if code_question is None:
            return JsonResponse({})

        # duplicate code question and link to assessment
