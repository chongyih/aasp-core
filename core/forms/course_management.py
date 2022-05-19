from datetime import datetime

from django import forms
from django.forms import models

from core.models import Course


class CourseForm(models.ModelForm):
    year = forms.ChoiceField(required=False)

    def __init__(self, years=None, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        if years:
            self.fields['year'].choices = years

    class Meta:
        model = Course
        fields = ['name', 'code', 'year', 'semester']
