# celery tasks
import requests
import cv2
import os
from celery import shared_task
from insightface.app import FaceAnalysis
from django.conf import settings
from django.utils import timezone

from core.models import TestCaseAttempt, CodeQuestionSubmission, AssessmentAttempt, CandidateSnapshot

@shared_task
def update_test_case_attempt_status(tca_id: int, token: str, last_status: int = 1):
    """
    Polls judge0 to get the status_id of a single submission (one test case)
    If status_id has been changed, save the change to db.
    If the submission is still being processed, re-queue this task to be polled again later.
    """
    try:
        # call judge0
        url = f"{settings.JUDGE0_URL}/submissions/{token}?base64_encoded=false&fields=status_id,stdout,time,memory"
        res = requests.get(url)
        data = res.json()

        status_id = data.get('status_id')
        stdout = data.get('stdout')
        time = data.get('time')
        memory = data.get('memory')

        if status_id is not None:
            # if status_id is different from the previous run of this task, update db
            if status_id != last_status:
                last_status = status_id
                tca = TestCaseAttempt.objects.prefetch_related('cq_submission').get(id=tca_id)
                tca.status = status_id
                tca.stdout = stdout
                tca.time = time
                tca.memory = memory
                tca.save()
                update_cqs_passed_flag.delay(tca.cq_submission.id)

            # if submission is still queued or processing, re-queue this task
            if status_id in [1, 2]:
                update_test_case_attempt_status.apply_async((tca_id, token, last_status), countdown=0.5)
    except ConnectionError:
        pass


@shared_task
def update_cqs_passed_flag(cqs_id):
    """
    Checks if all test cases of a CodeQuestionSubmission has been processed by judge0.
    Update the "passed" field of the CQS instance and initiates the computation of the submission score.
    If it was already calculated previously, nothing will be done.
    """
    # check if all test cases have been completed
    finished = not TestCaseAttempt.objects.filter(cq_submission_id=cqs_id, status__in=[1, 2]).exists()

    # only continue if test cases are complete
    if finished:
        # get cqs object
        cqs = CodeQuestionSubmission.objects.get(id=cqs_id)

        # only continue if it was not previously calculated
        if cqs.passed is None:
            # update the passed flag
            passed = not TestCaseAttempt.objects.filter(cq_submission_id=cqs_id, status__range=(4, 14)).exists()
            cqs.passed = passed
            cqs.save()


@shared_task
def force_submit_assessment(assessment_attempt_id):
    """
    Server-side submission of an assessment.
    This ensures that an AssessmentAttempt will be marked as submitted when the duration runs out, even if the user is not on the
    assessment page.
    If the AssessmentAttempt was already submitted previously (i.e. by the user), nothing will be done.
    """
    try:
        assessment_attempt = AssessmentAttempt.objects.get(id=assessment_attempt_id, time_submitted=None)
        if assessment_attempt:
            assessment_attempt.auto_submit = True  # set the auto_submit flag
            assessment_attempt.time_submitted = timezone.now()
            assessment_attempt.save()
            # queue task to compute score for this AssessmentAttempt
            compute_assessment_attempt_score.apply_async((assessment_attempt.id,), countdown=1)
    except:
        pass


@shared_task
def compute_assessment_attempt_score(assessment_attempt_id):
    """
    This task is queued when an AssessmentAttempt has been submitted (both user-initiated and server-side)
    This tasks calculates the total score of the AssessmentAttempt, and determines if it is the best attempt.
    If the AssessmentAttempt contains a submission that is still being processed, the task will be delayed.
    """
    try:
        # get the instance
        assessment_attempt = AssessmentAttempt.objects.get(id=assessment_attempt_id)
        
        # if all test cases are complete, proceed to compute score
        if not assessment_attempt.has_processing_submission():
            assessment_attempt.compute_score()
        # if still processing, queue it again with a 5s delay
        else:
            compute_assessment_attempt_score.apply_async((assessment_attempt_id,), countdown=5)
    except:
        pass


@shared_task
def detect_faces(snapshot_id):
    """
    This task is queued when candidate snapshot is uploaded.
    This task uses InsightFace to detect number of faces in the snapshot.
    """
    snapshot = CandidateSnapshot.objects.get(id=snapshot_id)
    image_path = os.path.join(settings.MEDIA_ROOT, snapshot.image.name)

    model_pack_name = "buffalo_l"
    app = FaceAnalysis(name=model_pack_name)
    app.prepare(ctx_id=0, det_size=(640, 640))
    image = cv2.imread(image_path)
    faces = app.get(image)

    snapshot.faces_detected = len(faces)
    snapshot.save()

    # rimg = app.draw_on(image, faces)
    # cv2.imwrite(image_path, rimg)
