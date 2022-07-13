from django.db import models


class AssessmentAttempt(models.Model):
    candidate = models.ForeignKey("User", null=False, blank=False, on_delete=models.PROTECT)
    assessment = models.ForeignKey("Assessment", null=False, blank=False, on_delete=models.PROTECT)
    time_started = models.DateTimeField(auto_now_add=True)
    time_submitted = models.DateTimeField(blank=True, null=True)
    auto_submit = models.BooleanField(blank=True, null=True)
    score = models.PositiveIntegerField(blank=True, null=True)

    def status(self):
        if self.time_started and not self.time_submitted:
            return "Started but not submitted"
        else:
            return "Unknown"


class CodeQuestionAttempt(models.Model):
    assessment_attempt = models.ForeignKey("AssessmentAttempt", null=False, blank=False, on_delete=models.PROTECT)
    code_question = models.ForeignKey("CodeQuestion", null=False, blank=False, on_delete=models.PROTECT)

    def answered(self):
        return CodeQuestionSubmission.objects.filter(cq_attempt=self).exists()


class CodeQuestionSubmission(models.Model):
    cq_attempt = models.ForeignKey("CodeQuestionAttempt", null=False, blank=False, on_delete=models.PROTECT)
    time_submitted = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField(blank=True, null=True)
    code = models.TextField()

    @property
    def outcome(self):
        if self.passed is None:
            return "Processing"
        elif self.passed:
            return "Passed"
        elif not self.passed:
            return "Failed"


class TestCaseAttempt(models.Model):
    STATUSES = [
        (1, "In Queue"),
        (2, "Processing"),
        (3, "Accepted"),
        (4, "Wrong Answer"),
        (5, "Time Limit Exceeded"),
        (6, "Compilation Error"),
        (7, "Runtime Error (SIGSEGV)"),
        (8, "Runtime Error (SIGXFSZ)"),
        (9, "Runtime Error (SIGFPE)"),
        (10, "Runtime Error (SIGABRT)"),
        (11, "Runtime Error (NZEC)"),
        (12, "Runtime Error (Other)"),
        (13, "Internal Error"),
        (14, "Exec Format Error"),
    ]

    cq_submission = models.ForeignKey("CodeQuestionSubmission", null=False, blank=False, on_delete=models.PROTECT)
    test_case = models.ForeignKey("TestCase", null=False, blank=False, on_delete=models.PROTECT)
    token = models.CharField(max_length=36, null=False, blank=False)
    status = models.IntegerField(choices=STATUSES, default=1)
