from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from core.forms.question_banks import CodeQuestionForm
from core.models import QuestionBank, Assessment, CodeQuestion
from core.models.questions import TestCase, CodeSnippet, Language
from core.views.utils import check_permissions, check_permissions_code_question


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
        if check_permissions(assessment.course, request.user) == 0:
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
            code_question = form.save()
            messages.success(request, "The code question has been created, please proceed to add some test cases!")
            return redirect('update-test-cases', code_question_id=code_question.id)

    context = {
        'assessment': assessment,
        'question_bank': question_bank,
        'description_placeholder': "# Heading 1\n## Heading 2\n\nThis editor supports **markdown**!\n",
        'form': form,
    }

    return render(request, 'code_questions/create-code-question.html', context)


@login_required()
def update_code_question(request, code_question_id):
    # get code question object
    code_question = get_object_or_404(CodeQuestion, id=code_question_id)

    # check permissions
    if check_permissions_code_question(code_question, request.user) == 0:
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
            print("valid fomr")
            form.save()
            messages.success(request, "Code Question successfully updated! ✅")

            if code_question.question_bank:
                return redirect('question-bank-details', question_bank_id=code_question.question_bank.id)
            else:
                # mytodo: redirect to assessment
                return redirect('')
        else:
            print("invalid form")

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
    if not check_permissions_code_question(code_question, request.user):
        messages.warning(request, "You do not have permissions to perform that action.")
        return redirect('dashboard')

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
    if not check_permissions_code_question(code_question, request.user):
        messages.warning(request, "You do not have permissions to perform that action.")
        return redirect('dashboard')

    # prepare formset
    CodeSnippetFormset = inlineformset_factory(CodeQuestion, CodeSnippet, extra=0, fields=['language', 'code'])
    code_snippet_formset = CodeSnippetFormset(prefix='cs', instance=code_question)

    # process POST requests
    if request.method == "POST":
        code_snippet_formset = CodeSnippetFormset(request.POST, instance=code_question, prefix='cs')
        if code_snippet_formset.is_valid():
            code_snippet_formset.save()
            messages.success(request, "Code Snippets saved!")

            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect('question-bank-details', question_bank_id=code_question.question_bank.id)

    context = {
        'creation': request.GET.get('next') is None,
        'code_question': code_question,
        'code_snippet_formset': code_snippet_formset,
        'languages': Language.objects.all(),
        'existing_languages': code_question.codesnippet_set.all().values_list('language', flat=True).distinct()
    }

    return render(request, 'code_questions/update-languages.html', context)
