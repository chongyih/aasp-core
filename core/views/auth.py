from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin

from core.forms.auth import MyAuthenticationForm


class Login(SuccessMessageMixin, LoginView):
    form_class = MyAuthenticationForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    success_message = "Welcome, you are successfully logged in!"


class Logout(LogoutView):
    pass
