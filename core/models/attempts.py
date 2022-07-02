from django.db import models
from django.utils import timezone


class AssessmentAttempt(models.Model):
    candidate = models.ForeignKey("User", null=False, blank=False, on_delete=models.PROTECT)
    assessment = models.ForeignKey("Assessment", null=False, blank=False, on_delete=models.PROTECT)
    time_started = models.DateTimeField(auto_now_add=True, editable=False)
    time_submitted = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(blank=True, null=True)

    def status(self):
        if self.time_started and not self.time_submitted:
            return "Started but not submitted"
        else:
            return "Unknown"
