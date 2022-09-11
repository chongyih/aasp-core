from django.core.validators import FileExtensionValidator
from django.forms import models, forms

from core.models import QuestionBank
from core.models.questions import TestCase, CodeQuestion


class QuestionBankForm(models.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['name', 'description', 'private']


class CodeQuestionForm(models.ModelForm):
    class Meta:
        model = CodeQuestion
        fields = ['name', 'description', 'question_bank', 'assessment']


class ImportQuestionBankForm(forms.Form):
    file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['json'])]
    )
