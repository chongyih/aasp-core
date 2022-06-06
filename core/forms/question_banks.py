from django.forms import models

from core.models import QuestionBank
from core.models.questions import TestCase


class QuestionBankForm(models.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['name', 'description', 'private']


class TestCaseForm(models.ModelForm):
    class Meta:
        model = TestCase
        fields = ['stdin', 'stdout', 'time_limit', 'memory_limit', 'marks', 'hidden', 'sample']

