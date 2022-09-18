from django.contrib.auth.decorators import login_required
from django.forms import models
from django import forms
from core.models import Assessment


class AssessmentForm(models.ModelForm):
    require_pin = forms.BooleanField(initial=False, required=False)

    class Meta:
        model = Assessment
        fields = ['course', 'name', 'time_start', 'time_end', 'duration', 'num_attempts', 'instructions', 'show_grade']

    def __init__(self, courses, *args, **kwargs):
        super(AssessmentForm, self).__init__(*args, **kwargs)
        self.fields['course'].queryset = courses
        self.fields['require_pin'].initial = self.instance.pin is not None

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data['time_start'] and cleaned_data['time_end']:
            # mytodo: ensure time start is before or same as time end
            pass

