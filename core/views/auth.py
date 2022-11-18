from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect

from core.forms.auth import MyAuthenticationForm


class Login(SuccessMessageMixin, LoginView):
    form_class = MyAuthenticationForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    success_message = "Welcome, you are successfully logged in!"


class Logout(LogoutView):
    pass


@login_required()
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # dont logout the user.
            messages.success(request, "Password changed.")
    else:
        form = PasswordChangeForm(user=request.user)

    context = {
        'form': form
    }

    return render(request, "auth/change-password.html", context)
