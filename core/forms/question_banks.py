from django.forms import models

from core.models import QuestionBank


class QuestionBankForm(models.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['name', 'description', 'private']
