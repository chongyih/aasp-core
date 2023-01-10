from django import forms
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.db import transaction
from django.core.exceptions import ValidationError

from core.models import User, Course, CourseGroup, Assessment
from core.views import assessments
from core.views.utils import is_student


class StudentCreationForm(forms.Form):
    """
    Form used for single student enrolment to a course.
    Creates a user account only if an account with the username does not exist yet.
    The user account is then added to the specified course group.
    """
    first_name = forms.CharField(max_length=150, required=True, strip=True)
    last_name = forms.CharField(max_length=150, required=True, strip=True)
    username = forms.CharField(max_length=150, required=True, strip=True)
    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=True)
    group = forms.CharField(max_length=20, required=True, strip=True)

    def __init__(self, courses, *args, **kwargs):
        super(StudentCreationForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = courses

    def clean_first_name(self):
        return self.cleaned_data['first_name'].upper()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].upper()

    def clean_username(self):
        return self.cleaned_data['username'].upper()

    def clean_group(self):
        return self.cleaned_data['group'].upper()

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        user = User.objects.filter(username=cleaned_data['username']).first()

        if user:
            # ensure user is a student
            if not is_student(user):
                raise ValidationError(f"The user with username '{user.username}' is not a student.")

            # ensure student not enrolled in the course yet
            if course.coursegroup_set.filter(students=user).exists():
                raise ValidationError("This student is already enrolled in the course.")

    def save(self):
        # ensures that changes are rolled back if any operation fails
        with transaction.atomic():
            # check if user already exists
            user = User.objects.filter(username=self.cleaned_data['username']).first()

            # create only if user does not exist
            if not user:
                user = User(
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    username=self.cleaned_data['username'],
                )

                user.email = f"{user.username}@E.NTU.EDU.SG"
                user.password = make_password(settings.DEFAULT_STUDENT_PASSWORD)
                user.save()

                # add user to the student group
                Group.objects.get(name="student").user_set.add(user)

            course = self.cleaned_data.get("course")
            course_group, _ = CourseGroup.objects.get_or_create(course=course, name=self.cleaned_data.get("group"))
            course_group.students.add(user)

            # if there are any published test(s), send email notification
            courses_assessments = Assessment.objects.filter(course=course, published=True, deleted=False).all()
            if courses_assessments:
                for a in courses_assessments:
                    assessments.send_assessment_published_email(assessment=a, recipients=[user])

            return user

