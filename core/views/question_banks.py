from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.forms import formset_factory, inlineformset_factory
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404

from core.forms.question_banks import QuestionBankForm, CodeQuestionForm
from core.models import QuestionBank, Assessment, User, CodeQuestion
from core.models.questions import TestCase, CodeSnippet, Language
from core.views.utils import check_permissions_qb, check_permissions, check_permissions_code_question


@login_required()
def view_question_banks(request):
    # all question banks (public/private) owned by the current user
    owned_question_banks = QuestionBank.objects.filter(owner=request.user)

    # private question banks that were shared with the current user
    shared_question_banks = QuestionBank.objects.filter(shared_with=request.user, private=True)

    # all public question banks regardless of ownership
    public_question_banks = QuestionBank.objects.filter(private=False)

    context = {
        'owned_qbs': owned_question_banks,
        'shared_qbs': shared_question_banks,
        'public_qbs': public_question_banks,
    }

    return render(request, 'question_banks/question_banks.html', context)


@login_required()
def create_question_bank(request):
    # initialize form
    form = QuestionBankForm()

    # process POST request
    if request.method == "POST":
        form = QuestionBankForm(request.POST)
        if form.is_valid():
            created_qb = form.save(commit=False)
            created_qb.owner = request.user
            created_qb.save()
            messages.success(request, "The question bank has been created! ✅")
            return redirect('view-question-banks')

    context = {
        'form': form
    }

    return render(request, 'question_banks/create-question-bank.html', context)


@login_required()
def update_question_bank(request, question_bank_id):
    # get question bank object
    question_bank = get_object_or_404(QuestionBank.objects.prefetch_related('owner'), id=question_bank_id)

    # check permissions of question bank
    if check_permissions_qb(question_bank, request.user) != 2:
        messages.warning(request, "You do not have permissions to update the question bank.")
        return redirect('view-question-banks')

    # initialize form with question bank instance
    form = QuestionBankForm(instance=question_bank)

    # process POST request
    if request.method == "POST":
        form = QuestionBankForm(request.POST, instance=question_bank)

        if form.is_valid():
            form.save()
            messages.success(request, "The question bank has been updated! ✅")

            # redirect to where the user came from
            next_url = request.GET.get("next")
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                return redirect('view-question-banks')

    context = {
        'form': form,
    }

    return render(request, 'question_banks/update-question-bank.html', context)


@login_required()
def question_bank_details(request, question_bank_id):
    # get question bank object
    question_bank = get_object_or_404(QuestionBank.objects.prefetch_related('owner', 'shared_with'), id=question_bank_id)

    # if no permissions, redirect back to course page
    if check_permissions_qb(question_bank, request.user) == 0:
        messages.warning(request, "You do not have permissions to view this question bank.")
        return redirect('view-question-banks')

    # get a list of staff accounts (educator/lab_assistant/superuser role)
    staff = User.objects.filter(Q(groups__name__in=('educator', 'lab_assistant')) | Q(is_superuser=True))

    context = {
        'question_bank': question_bank,
        'staff': staff,
    }

    return render(request, 'question_banks/question-bank-details.html', context)


@login_required()
def update_qb_shared_with(request):
    """
    Function to share/unshare a question bank with a user.
    Front-end does not display error messages for this feature, thus only the result of the operation is returned.
    """
    if request.method == "POST":
        # default error response
        error_context = {"result": "error", }

        # get params
        question_bank_id = request.POST.get("question_bank_id")
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        # missing params
        if question_bank_id is None or user_id is None or action is None:
            return JsonResponse(error_context, status=200)

        # get question bank object
        question_bank = QuestionBank.objects.filter(id=question_bank_id).prefetch_related('owner', 'shared_with').first()

        # question bank not found
        if not question_bank:
            return JsonResponse(error_context, status=200)

        # check if user has permissions for this question bank
        if check_permissions_qb(question_bank, request.user) != 2:
            return JsonResponse(error_context, status=200)

        # get user object
        user = User.objects.filter(id=user_id).first()

        # if user not found
        if not user:
            return JsonResponse(error_context, status=200)

        # add user to question bank
        if action == "add":
            question_bank.shared_with.add(user)
        elif action == "remove":
            question_bank.shared_with.remove(user)
        else:
            return JsonResponse(error_context, status=200)

        # return success
        return JsonResponse({"result": "success"}, status=200)


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
                                                fields=['stdin', 'stdout', 'time_limit', 'memory_limit', 'score', 'hidden', 'sample'])
    else:
        TestCaseFormset = inlineformset_factory(CodeQuestion, TestCase, extra=0,
                                                fields=['stdin', 'stdout', 'time_limit', 'memory_limit', 'score', 'hidden', 'sample'])
    testcase_formset = TestCaseFormset(prefix='tc', instance=code_question)

    # process POST requests
    if request.method == "POST":
        testcase_formset = TestCaseFormset(request.POST, instance=code_question, prefix='tc')
        if testcase_formset.is_valid():
            print("valid form")
            testcase_formset.save()
            messages.success(request, "Test cases updated!")
            return redirect('update-languages', code_question_id=code_question.id)
        else:
            print("invalid form!")

    context = {
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
            print("valid form")
            code_snippet_formset.save()
            messages.success(request, "Code Snippets saved!")
            return redirect('question-bank-details', question_bank_id=code_question.question_bank.id)
        else:
            print("invalid form!")

    context = {
        'code_question': code_question,
        'code_snippet_formset': code_snippet_formset,
        'languages': Language.objects.all(),
        'existing_languages': code_question.codesnippet_set.all().values_list('language', flat=True).distinct()
    }

    return render(request, 'code_questions/update-languages.html', context)
