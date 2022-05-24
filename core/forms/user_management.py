from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.db import transaction

from core.models import User, Course


class StudentCreationForm(forms.ModelForm):

    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=True)

    def __init__(self, courses, *args, **kwargs):
        super(StudentCreationForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = courses

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username")

    def save(self, commit=True):
        # ensures that changes are rolled back if any operation fails
        with transaction.atomic():
            # create user with parent save()
            user = super(StudentCreationForm, self).save(commit=True)

            # set email automatically based on username
            user.email = f"{user.username}@E.NTU.EDU.SG"

            # set default password (configured in project settings file)
            user.password = make_password(settings.DEFAULT_STUDENT_PASSWORD)

            # save changes
            user.save()

            # add user to the student group
            Group.objects.get(name="student").user_set.add(user)

            # add user to course
            self.cleaned_data.get("course").students.add(user)

            return user
