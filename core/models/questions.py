from django.core.exceptions import ValidationError
from django.db import models

from core.models import User, Assessment


class Language(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False)

    def clean(self):
        super().clean()
        self.name = self.name.upper()


class QuestionBank(models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name="owned_qbs")
    private = models.BooleanField(default=True, blank=False, null=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name="qbs_shared_with_me")

    def __str__(self):
        return self.name


class CodeQuestion(models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=False, null=False)
    sample_in = models.CharField(max_length=250, blank=False, null=False)
    sample_out = models.CharField(max_length=250, blank=False, null=False)
    sample_explanation = models.TextField(blank=False, null=False)

    # foreign keys (either linked to a QuestionBank or Assessment instance)
    question_bank = models.ForeignKey(QuestionBank, null=True, blank=True, on_delete=models.PROTECT)
    assessment = models.ForeignKey(Assessment, null=True, blank=True, on_delete=models.PROTECT)

    def clean(self):
        """
        Custom validation to ensure at least one foreign key is not null, but not both.
        """
        if not self.question_bank and not self.assessment:
            raise ValidationError("The question must be linked to either a Question Bank or an Assessment instance.")
        elif self.question_bank and self.assessment:
            raise ValidationError("The question cannot be be linked to both a Question Bank and an Assessment instance.")


class CodeSnippet(models.Model):
    class Meta:
        pass

    code_question = models.ForeignKey(CodeQuestion, null=False, blank=False, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, null=False, blank=False, on_delete=models.CASCADE)
    code = models.TextField(blank=False, null=False)


class TestCase(models.Model):
    class Meta:
        pass

    code_question = models.ForeignKey(CodeQuestion, null=False, blank=False, on_delete=models.CASCADE)
    stdin = models.TextField(blank=False, null=False)
    stdout = models.TextField(blank=False, null=False)
    marks = models.PositiveIntegerField()
    time_limit = models.PositiveIntegerField()
    memory_limit = models.PositiveIntegerField()
    hidden = models.BooleanField(default=True)
