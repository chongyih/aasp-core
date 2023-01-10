import random

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer

from core.decorators import groups_allowed, UserGroup
from core.filters import CodeQuestionFilter
from core.forms.assessments import AssessmentForm
from core.models import Course, Assessment, CodeQuestion, TestCase, CodeSnippet, Tag, QuestionBank, CourseGroup, User
from core.serializers import CodeQuestionsSerializer
from core.views.utils import check_permissions_course, check_permissions_assessment, check_permissions_code_question


@login_required()
@groups_allowed(UserGroup.educator)
def create_assessment(request):
    # get course_id if exists (optional)
    course_id = request.GET.get('course_id')

    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct().prefetch_related(
        'owner', 'maintainers')

    # form
    form = AssessmentForm(courses=courses, initial={'course': course_id})

    # process POST request
    if request.method == "POST":
        form = AssessmentForm(courses, request.POST)

        if form.is_valid():
            # get course object
            course = get_object_or_404(Course, id=form.data['course'])

            # check permissions before saving form
            if check_permissions_course(course, request.user) == 0:
                raise PermissionDenied("You do not have permissions for this course.")

            assessment = form.save(commit=False)
            if form.cleaned_data['require_pin'] is False:  # remove pin
                assessment.pin = None
            else:
                assessment.pin = random.randint(100_000, 999_999)  # generate random 6-digit pin
            assessment.save()

            # redirect
            messages.success(request, "The assessment has been successfully created!")
            return redirect('assessment-details', assessment_id=assessment.id)

    context = {
        'form': form,
    }

    return render(request, 'assessments/create-assessment.html', context)


@login_required()
@groups_allowed(UserGroup.educator)
def update_assessment(request, assessment_id):
    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct().prefetch_related(
        'owner', 'maintainers')

    # get assessment
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # check permissions
    if check_permissions_assessment(assessment, request.user) == 0:
        raise PermissionDenied("You do not have permissions for this course.")

    # form
    form = AssessmentForm(courses=courses, instance=assessment)

    # process POST request
    if request.method == "POST":
        form = AssessmentForm(courses, request.POST, instance=assessment)
        if form.is_valid():
            # get course object
            course = get_object_or_404(Course, id=form.data['course'])

            # check permissions before saving form
            if check_permissions_course(course, request.user) == 0:
                raise PermissionDenied("You do not have permissions for this course.")

            # update pin
            assessment = form.save(commit=False)
            if form.cleaned_data['require_pin'] is False:  # remove pin
                assessment.pin = None

            # only generate new pin if it was previously not required
            elif form.cleaned_data['require_pin'] is True and assessment.pin is None:
                assessment.pin = random.randint(100_000, 999_999)  # generate random 6-digit pin

            assessment.save()

            # redirect
            messages.success(request, "The assessment has been successfully updated!")
            return redirect('assessment-details', assessment_id=assessment.id)

    context = {
        'form': form,
        'assessment': assessment,
    }
    return render(request, 'assessments/update-assessment.html', context)


@login_required()
@groups_allowed(UserGroup.educator, UserGroup.lab_assistant)
def assessment_details(request, assessment_id):
    # get assessment object
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # check permissions
    if check_permissions_assessment(assessment, request.user) == 0:
        raise PermissionDenied("You do not have permissions to view this assessment.")

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
@groups_allowed(UserGroup.educator)
def get_code_questions(request):
    """
    Used in the Assessment Details page for educators to clone questions from question banks into assessments.
    """
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
@groups_allowed(UserGroup.educator)
def add_code_question_to_assessment(request):
    if request.method == "POST":
        # generic error response
        error_context = {"result": "error", }

        # get assessment object
        assessment = Assessment.objects.filter(id=request.POST.get('assessment_id')).first()
        if assessment is None:
            return JsonResponse(error_context, status=200)

        # check permissions
        if check_permissions_assessment(assessment, request.user) == 0:
            return JsonResponse(error_context, status=200)

        # disallow if assessment is already published
        if assessment.published:
            return JsonResponse(error_context, status=200)

        # get question (ensure only objects from question banks are allowed)
        code_question_id = request.POST.get('code_question_id')
        code_question = CodeQuestion.objects.filter(id=code_question_id, assessment__isnull=True,
                                                    question_bank__isnull=False).first()
        if code_question is None:
            return JsonResponse(error_context, status=200)

        tags = code_question.tags.all()

        # check permissions (need at least Read permissions to clone)
        if check_permissions_code_question(code_question, request.user) == 0:
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

            # remove past assessment attempts
            assessment.assessmentattempt_set.all().delete()

        return JsonResponse({"result": "success"}, status=200)


@login_required()
@groups_allowed(UserGroup.educator)
def publish_assessment(request, assessment_id):
    if request.method == "POST":
        # get assessment object
        assessment = get_object_or_404(Assessment, id=assessment_id)

        # check permissions
        if check_permissions_assessment(assessment, request.user) == 0:
            raise PermissionDenied("You do not have permissions to modify this assessment.")

        if not assessment.published:
            # check if all questions are valid
            publishable, msg = assessment.is_valid()
            if not publishable:
                messages.warning(request, f"Not published! {msg}")
                return redirect("assessment-details", assessment_id=assessment_id)

            with transaction.atomic():
                # delete attempts
                assessment.assessmentattempt_set.all().delete()

                # publish assessment
                assessment.published = True
                assessment.save()
            
            try:
                # send email notification to students enrolled
                send_assessment_published_email(assessment)
                messages.success(request, "The assessment has been published!")
            except Exception as ex:
                messages.warning(request, f"{ex}")

        else:
            messages.warning(request, "The assessment is already published!")
            
        return redirect("assessment-details", assessment_id=assessment_id)


@login_required()
@groups_allowed(UserGroup.educator)
def delete_assessment(request, assessment_id):
    if request.method == "POST":
        # get assessment
        assessment = get_object_or_404(Assessment, id=assessment_id)

        # check permissions (only course owner/maintainer can delete)
        if check_permissions_assessment(assessment, request.user) == 0:
            raise PermissionDenied("You do not have permissions to modify this assessment.")
        else:
            if assessment.deleted:
                messages.warning(request, "Assessment was already deleted!")
            else:
                assessment.deleted = True
                assessment.save()
                messages.success(request, "Assessment successfully deleted!")
            return redirect('assessment-details', assessment_id=assessment_id)


@login_required()
@groups_allowed(UserGroup.educator)
def undo_delete_assessment(request, assessment_id):
    if request.method == "POST":
        # get assessment
        assessment = get_object_or_404(Assessment, id=assessment_id)

        # check permissions (only course owner/maintainer can delete)
        if check_permissions_assessment(assessment, request.user) == 0:
            raise PermissionDenied("You do not have permissions to modify this assessment.")
        else:
            if assessment.deleted is False:
                messages.warning(request, "Assessment was not deleted, no undo needed!")
            else:
                assessment.deleted = False
                assessment.save()
                messages.success(request, "Undo delete successful!")
            return redirect('assessment-details', assessment_id=assessment_id)


def send_assessment_published_email(assessment, recipients=None):
    course_groups = CourseGroup.objects.filter(course=assessment.course).prefetch_related('course')
    students_enrolled = User.objects.filter(enrolled_groups__in=course_groups)

    if recipients is None and not students_enrolled.exists:
        return

    if recipients is None:
        recipients = students_enrolled
    
    subject = f"{assessment.course} {assessment.name} Published"

    connection = mail.get_connection()
    connection.open()
    for student in recipients:
        text_content = f"Dear {student.get_full_name()},\n {assessment.name}\n{assessment.course}"
        html_content = f"Dear {student.get_full_name()},\
                        <p><b>{assessment.name}</b></p>\
                        <p>{assessment.course}</p>"
        
        send_email(subject, text_content, html_content, [student.email])
    connection.close()
    

def send_email(subject, text_content, html_content, recipient):
    try:
        email = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, recipient)
        email.attach_alternative(html_content, "text/html")
        
        email.send()
        
    except:
        raise EmailException()


class EmailException(Exception):
    def __str__(self):
        return f"An error occurred. Please try again."


@api_view(["POST"])
@renderer_classes([JSONRenderer])
def send_email_test_api(request):
    try:
        assessment_id = request.POST.get('assessment_id')
        assessment = Assessment.objects.get(id=assessment_id)
        send_assessment_published_email(assessment)

        return Response({ "result": "success" }, status=status.HTTP_200_OK)

    except Exception as ex:
        context = { 
            "result": "error",
            "exception": f"{ex}"
            }
        return Response(context, status=status.HTTP_400_BAD_REQUEST)

