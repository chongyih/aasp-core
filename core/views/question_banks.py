from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404

from core.forms.question_banks import QuestionBankForm
from core.models import QuestionBank
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
        messages.warning(request, "You do not have permissions to update the question bank.")
        return redirect('view-question-banks')

    context = {
        'question_bank': question_bank,

    }

    return render(request, 'question_banks/question-bank-details.html', context)