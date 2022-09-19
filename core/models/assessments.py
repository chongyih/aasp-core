from django.apps import apps
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Assessment(models.Model):
    course = models.ForeignKey("Course", null=False, blank=False, on_delete=models.PROTECT)
    name = models.CharField(max_length=150, null=False, blank=False)
    time_start = models.DateTimeField(null=True, blank=True)  # null if forever
    time_end = models.DateTimeField(null=True, blank=True)  # null if forever
    duration = models.PositiveIntegerField(null=False, blank=False)  # 0 if unlimited
    num_attempts = models.PositiveIntegerField(null=False, blank=False)  # 0 if unlimited
    instructions = models.TextField(null=False, blank=False)
    deleted = models.BooleanField(default=False)
    show_grade = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    pin = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    @property
    def status(self):
        """
        Unpublished, Deleted, Active, Upcoming, Ended
        """
        if self.published is False:
            return "Unpublished"
        if self.deleted:
            return "Deleted"
        if self.time_start is None and self.time_end is None:  # unlimited duration (no time_start and no time_end)
            return "Active"
        if self.time_start and timezone.now() < self.time_start:  # upcoming (it is before time_start)
            return "Upcoming"
        if (self.time_start and self.time_end) and self.time_start <= timezone.now() <= self.time_end:  # active (it is between start and end)
            return "Active"
        if self.time_end and timezone.now() > self.time_end:  # ended (it is past time_end)
            return "Ended"
        raise Exception("Unknown course status!")

    def is_valid(self):
        """
        Returns if an assessment is valid or not.
        - (True, ""), if assessment contains questions and questions are complete.
        - (False, <error_message>), if otherwise.
        """
        CodeQuestion = apps.get_model(app_label="core", model_name="CodeQuestion")
        code_questions = CodeQuestion.objects.filter(assessment=self)

        # ensure assessment has at least one question
        if not code_questions:
            return False, "There are no questions in the assessment."

        # ensure all code questions has at least one test case and one code snippet (language)
        for cq in code_questions:
            if cq.testcase_set.count() == 0 or cq.codesnippet_set.count() == 0:
                return False, "One or more code questions are incomplete."

        return True, ""

    @property
    def total_score(self):
        TestCase = apps.get_model(app_label="core", model_name="TestCase")
        total_score = TestCase.objects.filter(code_question__assessment=self).aggregate(Sum('score')).get("score__sum", 0)
        return total_score
