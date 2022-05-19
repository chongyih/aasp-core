from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.db import transaction

from core.models import User, Course


class StudentCreationForm(UserCreationForm):

    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=False)

    def __init__(self, courses, *args, **kwargs):
        super(StudentCreationForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = courses
        print(courses)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "identification", "password1", "password2")

    def save(self, commit=True):
        # ensures that changes are rolled back if any operation fails
        with transaction.atomic():
            # create user with parent save()
            user = super(StudentCreationForm, self).save(commit=True)

            # add user to the student group
            Group.objects.get(name="student").user_set.add(user)

            # add user to course
            self.cleaned_data.get("course").students.add(user)

            return user
