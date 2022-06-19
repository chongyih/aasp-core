from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from core.models import User, Assessment


class Tag(models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=50, blank=False, null=False, unique=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.name = self.name.title()


class Language(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False, unique=True)
    judge_language_id = models.IntegerField(blank=False, null=False)

    def clean(self):
        super().clean()
        self.name = self.name.upper()

    def __str__(self):
        return self.name


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
    tags = models.ManyToManyField(Tag, blank=True)

    # foreign keys (either linked to a QuestionBank or Assessment instance)
    question_bank = models.ForeignKey(QuestionBank, null=True, blank=True, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, null=True, blank=True, on_delete=models.PROTECT)

    def clean(self):
        """
        Custom validation to ensure at least one foreign key is not null, but not both.
        """
        if not self.question_bank and not self.assessment:
            raise ValidationError("The question must be linked to either a Question Bank or an Assessment instance.")
        elif self.question_bank and self.assessment:
            raise ValidationError("The question cannot be be linked to both a Question Bank and an Assessment instance.")

    def __str__(self):
        return self.name

    def max_score(self):
        total = self.testcase_set.all().aggregate(Sum('score')).get('score__sum')
        if total is None:
            total = 0
        return total


class CodeSnippet(models.Model):
    class Meta:
        pass

    code_question = models.ForeignKey(CodeQuestion, null=False, blank=False, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, null=False, blank=False, on_delete=models.CASCADE)
    code = models.TextField(blank=True, null=True)


class TestCase(models.Model):
    """
    Two types of test cases: Sample and Internal
      - Sample: displayed to the user together with the problem description, has no score.
      - Internal: input/output are hidden by default, has score.
    """

    class Meta:
        pass

    code_question = models.ForeignKey(CodeQuestion, null=False, blank=False, on_delete=models.CASCADE)
    stdin = models.TextField(blank=False, null=False)
    stdout = models.TextField(blank=False, null=False)
    time_limit = models.PositiveIntegerField()
    memory_limit = models.PositiveIntegerField()

    score = models.PositiveIntegerField()
    hidden = models.BooleanField(default=True)
    sample = models.BooleanField(default=False)


class CodeTemplate(models.Model):
    class Meta:
        pass

    language = models.ForeignKey(Language, null=False, blank=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=False, null=False)
    code = models.TextField(blank=False, null=False)
