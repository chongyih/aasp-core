from django.db import models
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

    def __str__(self):
        return f"{self.name}"

    def status(self):
        if self.deleted:
            return "Deleted"
        elif not self.time_start and not self.time_end:
            return "Active"
        elif self.time_start and timezone.now() < self.time_start:  # not started yet
            return "Not started"
        elif self.time_start and self.time_end and self.time_start <= timezone.now() <= self.time_end:
            return "Active"
        elif self.time_end and timezone.now() > self.time_end:
            return "Finished"
        else:
            return "Active"


class AssessmentAttempt(models.Model):
    assessment = models.ForeignKey(Assessment, null=False, blank=False, on_delete=models.PROTECT)
    candidate = models.ForeignKey("User", null=False, blank=False, on_delete=models.PROTECT)
    time_started = models.DateTimeField(auto_now_add=True, editable=False)
    time_submitted = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(blank=True, null=True)

    def status(self):
        if self.time_started and not self.time_submitted:
            return "Started but not submitted"

