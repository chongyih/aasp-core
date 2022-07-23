from django.contrib.auth.forms import AuthenticationForm


class MyAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        return self.cleaned_data['username'].upper()
