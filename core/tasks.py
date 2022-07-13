# celery tasks
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from core.models import TestCaseAttempt, CodeQuestionSubmission, AssessmentAttempt


@shared_task
def update_test_case_attempt_status(tca_id: int, token: str, last_status: int = 1):
    """
    Polls judge0 to get the status_id of a single submission (one test case)
    If status_id has been changed, save the change to db.
    If the submission is still being processed, re-queue this task to be polled again later.
    """
    try:
        # call judge0
        url = f"{settings.JUDGE0_URL}/submissions/{token}?base64_encoded=false&fields=status_id"
        res = requests.get(url)
        status_id = res.json().get('status_id')

        if status_id is not None:
            # if status_id is different from the previous run of this task, update db
            if status_id != last_status:
                last_status = status_id
                tca = TestCaseAttempt.objects.get(id=tca_id)
                tca.status = status_id
                tca.save()

            # if submission is still queued or processing, re-queue this task
            if status_id in [1, 2]:
                update_test_case_attempt_status.delay(tca_id, token, last_status)
    except ConnectionError:
        pass


@shared_task
def update_cqa_finished_flag(cqs_id):
    """
    Checks if all test cases of a CodeQuestionSubmission has been processed by judge0.
    If so, update the "finished" field of the CQS instance.
    Else, re-queue this task to be checked again later.
    """
    # check if all test cases have are completed
    finished = not TestCaseAttempt.objects.filter(cq_submission_id=cqs_id, status__in=[1, 2]).exists()

    # if finished, update db
    if finished:
        passed = not TestCaseAttempt.objects.filter(cq_submission_id=cqs_id, status__range=(4, 14)).exists()
        cqs = CodeQuestionSubmission.objects.get(id=cqs_id)
        cqs.passed = passed
        cqs.save()
    else:
        update_cqa_finished_flag.delay(cqs_id)


@shared_task
def force_submit_assessment(assessment_attempt_id):
    assessment_attempt = AssessmentAttempt.objects.get(id=assessment_attempt_id)
    if assessment_attempt.auto_submit is None and assessment_attempt.time_submitted is None:
        assessment_attempt.auto_submit = True
        assessment_attempt.time_submitted = timezone.now()
        assessment_attempt.save()
