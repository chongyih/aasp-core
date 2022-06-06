from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from core.forms.question_banks import QuestionBankForm, TestCaseForm
from core.models import QuestionBank, Assessment, User
from core.views.utils import check_permissions_qb


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
def create_code_question(request):
    """
    Allows the user to create a code question for either a question bank, or an assessment.
    Thus, a question bank id or assessment id must be passed as a GET parameter, but not both.
    """
    # check validity of question bank or assessment id
    qb_id = request.GET.get('qb_id')
    assessment_id = request.GET.get('assessment_id')
    if qb_id is not None and assessment_id is not None:
        messages.warning(request, "Something went wrong, both qb and assessment IDs were passed to the view.")
        return redirect('dashboard')
    elif qb_id is None and assessment_id is None:
        messages.warning(request, "Something went wrong, no qb or assessment ID were passed to the view.")
        return redirect('dashboard')

    # get question bank or assessment object
    question_bank = None
    assessment = None
    if qb_id is not None:
        question_bank = get_object_or_404(QuestionBank, id=qb_id)
    else:
        assessment = get_object_or_404(Assessment, id=assessment_id)

    # formset
    TestCaseFormset = formset_factory(TestCaseForm)
    testcase_formset = TestCaseFormset(prefix='tc')

    if request.method == "POST":
        pass

    context = {
        'question_bank': question_bank,
        'assessment': assessment,
        'description_placeholder': "# Heading 1\n## Heading 2\n\nThis editor supports **markdown**!\n",
        'testcase_formset': testcase_formset,
    }

    return render(request, 'code_questions/create-code-question.html', context)


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
