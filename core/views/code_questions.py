from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer

from core.decorators import groups_allowed, UserGroup
from core.forms.question_banks import CodeQuestionForm
from core.models import QuestionBank, Assessment, CodeQuestion
from core.models.questions import TestCase, CodeSnippet, Language, Tag
from core.serializers import CodeQuestionsSerializer
from core.views.utils import check_permissions_course, check_permissions_code_question


@login_required()
@groups_allowed(UserGroup.educator)
def create_code_question(request, parent, parent_id):
    """
    For creating a new code question.
    Parent is either a Question Bank or an Assessment.
    """
    question_bank = None
    assessment = None

    # get object instance and check permissions
    if parent == "qb":
        question_bank = get_object_or_404(QuestionBank, id=parent_id)

        # the user must be the question bank's owner
        if question_bank.owner != request.user:
            return PermissionDenied("You do not have permissions to modify this question bank.")

    elif parent == "as":
        assessment = get_object_or_404(Assessment, id=parent_id)

        # the user must have permissions to the course
        if check_permissions_course(assessment.course, request.user) == 0:
            return PermissionDenied("You do not have permissions to modify this assessment.")

    else:
        raise Http404()

    # create form
    form = CodeQuestionForm()

    # process POST requests
    if request.method == "POST":
        form = CodeQuestionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # create tags
                tags = request.POST.get('tags')
                tags = [t.title() for t in tags.split(",")]
                if tags:
                    Tag.objects.bulk_create([Tag(name=t) for t in tags], ignore_conflicts=True)

                # save code question
                code_question = form.save()

                # add tags to code question
                tags = Tag.objects.filter(name__in=tags).values_list('id', flat=True)
                code_question.tags.add(*tags)

                messages.success(request, "The code question has been created, please proceed to add some test cases!")
                return redirect('update-test-cases', code_question_id=code_question.id)

    context = {
        'assessment': assessment,
        'question_bank': question_bank,
        'description_placeholder': """This editor supports **markdown**! And math equations too!

You can do this: $a \\ne 0$, and this:
$$x = {-b \pm \sqrt{b^2-4ac} \over 2a}$$

**Click preview!**""",
        'form': form,
    }

    return render(request, 'code_questions/create-code-question.html', context)


@login_required()
@groups_allowed(UserGroup.educator)
def update_code_question(request, code_question_id):
    # get code question object
    code_question = get_object_or_404(CodeQuestion, id=code_question_id)

    # check permissions
    if check_permissions_code_question(code_question, request.user) != 2:
        if code_question.question_bank:
            return PermissionDenied("You do not have permissions to modify this question bank.")
        else:
            return PermissionDenied("You do not have permissions to modify this assessment.")

    # prepare form
    form = CodeQuestionForm(instance=code_question)

    # handle POST request
    if request.method == "POST":
        form = CodeQuestionForm(request.POST, instance=code_question)

        if form.is_valid():
            with transaction.atomic():
                # create tags
                tags = request.POST.get('tags')
                tags = [t.title() for t in tags.split(",")]
                if tags:
                    Tag.objects.bulk_create([Tag(name=t) for t in tags], ignore_conflicts=True)

                code_question = form.save()
                messages.success(request, "Code Question successfully updated!")

                # clear old tags and add tags to code question
                code_question.tags.clear()
                tags = Tag.objects.filter(name__in=tags).values_list('id', flat=True)
                code_question.tags.add(*tags)

                if code_question.question_bank:
                    return redirect('question-bank-details', question_bank_id=code_question.question_bank.id)
                else:
                    return redirect('assessment-details', assessment_id=code_question.assessment.id)

    context = {
        'code_question': code_question,
        'form': form,
    }

    return render(request, 'code_questions/update-code-question.html', context)


@login_required()
@groups_allowed(UserGroup.educator)
def update_test_cases(request, code_question_id):
    # get CodeQuestion instance
    code_question = get_object_or_404(CodeQuestion, id=code_question_id)

    # check permissions
    if check_permissions_code_question(code_question, request.user) != 2:
        return PermissionDenied()

    # if belongs to a published assessment, disallow
    if code_question.assessment and code_question.assessment.published:
        messages.warning(request, "Test cases from a published assessment cannot be modified!")
        return redirect('assessment-details', assessment_id=code_question.assessment.id)

    # prepare formset
    if code_question.testcase_set.count() == 0:
        TestCaseFormset = inlineformset_factory(CodeQuestion, TestCase, extra=3,
                                                fields=['stdin', 'stdout', 'time_limit', 'memory_limit', 'score',
                                                        'hidden', 'sample'])
    else:
        TestCaseFormset = inlineformset_factory(CodeQuestion, TestCase, extra=0,
                                                fields=['stdin', 'stdout', 'time_limit', 'memory_limit', 'score',
                                                        'hidden', 'sample'])
    testcase_formset = TestCaseFormset(prefix='tc', instance=code_question)

    # process POST requests
    if request.method == "POST":
        testcase_formset = TestCaseFormset(request.POST, instance=code_question, prefix='tc')
        if testcase_formset.is_valid():

            # remove past attempts
            if code_question.assessment:
                code_question.assessment.assessmentattempt_set.all().delete()

            testcase_formset.save()
            messages.success(request, "Test cases updated!")

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect('update-languages', code_question_id=code_question.id)

    context = {
        'creation': request.GET.get('next') is None,
        'code_question': code_question,
        'testcase_formset': testcase_formset,
    }
    return render(request, 'code_questions/update-test-cases.html', context)


@login_required()
@groups_allowed(UserGroup.educator)
def update_languages(request, code_question_id):
    # get CodeQuestion instance
    code_question = get_object_or_404(CodeQuestion, id=code_question_id)

    # check permissions
    if check_permissions_code_question(code_question, request.user) != 2:
        return PermissionDenied()

    # if belongs to a published assessment, disallow
    if code_question.assessment and code_question.assessment.published:
        messages.warning(request, "Languages from a published assessment cannot be modified!")
        return redirect('assessment-details', assessment_id=code_question.assessment.id)

    # prepare formset
    CodeSnippetFormset = inlineformset_factory(CodeQuestion, CodeSnippet, extra=0, fields=['language', 'code'])
    code_snippet_formset = CodeSnippetFormset(prefix='cs', instance=code_question)

    # process POST requests
    if request.method == "POST":
        code_snippet_formset = CodeSnippetFormset(request.POST, instance=code_question, prefix='cs')
        if code_snippet_formset.is_valid():

            # remove past attempts
            if code_question.assessment:
                code_question.assessment.assessmentattempt_set.all().delete()

            code_snippet_formset.save()
            messages.success(request, "Code Snippets saved!")

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            if code_question.question_bank:
                return redirect('question-bank-details', question_bank_id=code_question.question_bank.id)
            else:
                return redirect('assessment-details', assessment_id=code_question.assessment.id)

    context = {
        'creation': request.GET.get('next') is None,
        'code_question': code_question,
        'code_snippet_formset': code_snippet_formset,
        'languages': Language.objects.all(),
        'existing_languages': code_question.codesnippet_set.all().values_list('language', flat=True).distinct()
    }

    return render(request, 'code_questions/update-languages.html', context)


@api_view(["GET"])
@renderer_classes([JSONRenderer])
@login_required()
@groups_allowed(UserGroup.educator, UserGroup.lab_assistant)
def get_cq_details(request):
    try:
        error_context = {"result": "error", }

        if request.method == "GET":
            # get cq_id from request
            cq_id = request.GET.get("cq_id")

            # get code question object
            code_question = CodeQuestion.objects.filter(id=cq_id).first()

            # code question not found
            if not code_question:
                return Response(error_context, status=status.HTTP_404_NOT_FOUND)

            # check permissions
            if check_permissions_code_question(code_question, request.user) == 0:
                return Response(error_context, status=status.HTTP_401_UNAUTHORIZED)

            # prepare context and serialize code question
            context = {
                "result": "success",
                "code_question": CodeQuestionsSerializer(code_question, many=False).data
            }

            return Response(context, status=status.HTTP_200_OK)

    except Exception as ex:
        context = { 
            "result": "error",
            "message": f"{ex}"
            }
        return Response(context, status=status.HTTP_400_BAD_REQUEST)
