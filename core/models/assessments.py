from django.db import models


class Assessment(models.Model):
    course = models.ForeignKey("Course", null=False, blank=False, on_delete=models.PROTECT)
    name = models.CharField(max_length=150, null=False, blank=False)
    owner = models.ForeignKey("User", null=False, blank=False, on_delete=models.PROTECT)
    time_start = models.DateTimeField(null=True, blank=True)  # null if forever
    time_end = models.DateTimeField(null=True, blank=True)  # null if forever
    duration = models.PositiveIntegerField(null=True, blank=True)  # null if unlimited
    num_attempts = models.PositiveIntegerField(null=True, blank=True)  # null if unlimited
    instructions = models.TextField(null=False, blank=False)
    deleted = models.BooleanField(default=False)
    show_grade = models.BooleanField(default=False)


class AssessmentAttempt(models.Model):
    assessment = models.ForeignKey(Assessment, null=False, blank=False, on_delete=models.PROTECT)
    candidate = models.ForeignKey("User", null=False, blank=False, on_delete=models.PROTECT)
    time_started = models.DateTimeField(auto_now_add=True, editable=False)
    time_submitted = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(blank=True, null=True)

    def status(self):
        if self.time_started and not self.time_submitted:
            return "Started but not submitted"
