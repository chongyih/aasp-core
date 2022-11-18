from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.forms.question_banks import CodeQuestionForm
from core.models import QuestionBank, Assessment, CodeQuestion
from core.models.questions import TestCase, CodeSnippet, Language, Tag
from core.serializers import CodeQuestionsSerializer
from core.views.utils import check_permissions_course, check_permissions_code_question


@login_required()
def create_code_question(request, parent, parent_id):
    question_bank = None
    assessment = None

    # get object instance and check permissions
    if parent == "qb":
        question_bank = get_object_or_404(QuestionBank, id=parent_id)
        if question_bank.owner != request.user:
            messages.warning(request, "You do not have permissions for this question bank.")
            return redirect('view-question-banks')
    elif parent == "as":
        assessment = get_object_or_404(Assessment, id=parent_id)
        if check_permissions_course(assessment.course, request.user) == 0:
            messages.warning(request, "You do not have permissions for this course.")
            return redirect('view-courses')
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
                if tags:
                    # get a list of tags
                    tags = set([t.title() for t in tags.split(",")])

                    # get tags that already exist (so that we don't create them again)
                    existing_tags = set(Tag.objects.filter(name__in=tags).values_list('name', flat=True))

                    # create the new tags
                    new_tags = tags - existing_tags
                    new_tags = [Tag(name=t) for t in new_tags]
                    Tag.objects.bulk_create(new_tags)

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
        'description_placeholder': "This editor supports **markdown**!\n",
        'form': form,
    }

    return render(request, 'code_questions/create-code-question.html', context)


@login_required()
def update_code_question(request, code_question_id):
    # get code question object
    code_question = get_object_or_404(CodeQuestion, id=code_question_id)

    # check permissions
    if check_permissions_code_question(code_question, request.user) != 2:
        if code_question.question_bank:
            messages.warning(request, "You do not have permissions for this question bank.")
            return redirect('view-question-banks')
        else:
            messages.warning(request, "You do not have permissions for this course.")
            return redirect('view-courses')

    # prepare form
    form = CodeQuestionForm(instance=code_question)

    # handle POST request
    if request.method == "POST":
        form = CodeQuestionForm(request.POST, instance=code_question)

        if form.is_valid():
            with transaction.atomic():
                # create tags
                tags = request.POST.get('tags')
                if tags:
                    # get a list of tags
                    tags = set([t.title() for t in tags.split(",")])

                    # get tags that already exist (so that we don't create them again)
                    existing_tags = set(Tag.objects.filter(name__in=tags).values_list('name', flat=True))

                    # create the new tags
                    new_tags = tags - existing_tags
                    new_tags = [Tag(name=t) for t in new_tags]
                    Tag.objects.bulk_create(new_tags)

                code_question = form.save()
                messages.success(request, "Code Question successfully updated! ✅")

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
def update_test_cases(request, code_question_id):
    # get CodeQuestion instance
    code_question = get_object_or_404(CodeQuestion, id=code_question_id)

    # check permissions
    if check_permissions_code_question(code_question, request.user) != 2:
        messages.warning(request, "You do not have permissions to perform that action.")
        return redirect('dashboard')

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


def update_languages(request, code_question_id):
    # get CodeQuestion instance
    code_question = get_object_or_404(CodeQuestion, id=code_question_id)

    # check permissions
    if check_permissions_code_question(code_question, request.user) != 2:
        messages.warning(request, "You do not have permissions to perform that action.")
        return redirect('dashboard')

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


def get_cq_details(request):
    error_context = {"result": "error", }

    if request.method == "GET":
        # get cq_id from request
        cq_id = request.GET.get("cq_id")

        # get code question object
        code_question = CodeQuestion.objects.filter(id=cq_id).first()

        # code question not found
        if not code_question:
            return JsonResponse(error_context, status=200)

        # mytodo: check permissions

        # prepare context and serialize code question
        context = {
            "result": "success",
            "code_question": CodeQuestionsSerializer(code_question, many=False).data
        }

        return JsonResponse(context, status=200)
