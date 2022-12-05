import csv

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.text import slugify

from core.decorators import UserGroup, groups_allowed
from core.models import Assessment, AssessmentAttempt, CodeQuestionSubmission, TestCaseAttempt, TestCase
from core.views.utils import check_permissions_assessment


@login_required()
@groups_allowed(UserGroup.educator)
def assessment_report(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)

    best_attempts = AssessmentAttempt.objects \
                    .select_related("assessment") \
                    .filter(best_attempt=True).order_by("-score")
    ongoing_ungraded_attempts = AssessmentAttempt.objects \
                                .select_related("assessment") \
                                .filter(Q(time_submitted__isnull=True) | Q(time_submitted__isnull=False, score__isnull=True))

    context = {
        "assessment": assessment,
        "best_attempts": best_attempts,
        "ongoing_ungraded_attempts": ongoing_ungraded_attempts,
    }

    return render(request, "reports/assessment-report.html", context)


@login_required()
@groups_allowed(UserGroup.educator)
def get_candidate_attempts(request, assessment_id):
    # get candidate_id
    candidate_id = request.GET.get("candidate_id")
    if not candidate_id:
        return JsonResponse({"result": "error"}, status=200)

    # get assessment attempts
    assessment_attempts = AssessmentAttempt.objects \
        .filter(assessment__id=assessment_id, candidate__id=candidate_id, time_submitted__isnull=False) \
        .values("id", "time_started", "time_submitted", "auto_submit", "score", "best_attempt").order_by("id")

    # prepare context
    context = {
        "result": "success",
        "assessment_attempts": list(assessment_attempts)
    }
    return JsonResponse(context, status=200)


@login_required()
@groups_allowed(UserGroup.educator)
def assessment_attempt_details(request):
    assessment_attempt_id = request.GET.get("attempt_id")
    assessment_attempt = get_object_or_404(AssessmentAttempt, id=assessment_attempt_id)

    context = {
        "assessment_attempt": assessment_attempt
    }
    return render(request, "reports/assessment-attempt-details.html", context)


@login_required()
@groups_allowed(UserGroup.educator)
def submission_details(request, cqs_id):
    cqs = get_object_or_404(CodeQuestionSubmission, id=cqs_id)
    test_case_attempts = TestCaseAttempt.objects.filter(cq_submission=cqs).order_by('test_case__id')
    context = {
        'cqs': cqs,
        'test_case_attempts': test_case_attempts,
    }

    return render(request, "reports/submission-details.html", context)


@login_required()
@groups_allowed(UserGroup.educator)
def export_test_case_stdin(request):
    test_case_id = request.GET.get('test_case_id')
    test_case = get_object_or_404(TestCase, id=test_case_id)
    content = test_case.stdin
    filename = f"tc_{test_case.id}_stdin.txt"

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@login_required()
@groups_allowed(UserGroup.educator)
def export_test_case_stdout(request):
    test_case_id = request.GET.get('test_case_id')
    test_case = get_object_or_404(TestCase, id=test_case_id)
    content = test_case.stdout
    filename = f"tc_{test_case.id}_stdout.txt"

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@login_required()
@groups_allowed(UserGroup.educator)
def export_test_case_attempt_stdout(request, tca_id):
    tca = get_object_or_404(TestCaseAttempt, id=tca_id)
    content = tca.stdout
    filename = f"tca_{tca.id}_stdout.txt"

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@login_required()
@groups_allowed(UserGroup.educator)
def export_assessment_results(request, assessment_id):
    # check that assessment exist
    assessment = get_object_or_404(Assessment.objects.select_related("course"), id=assessment_id)

    # check permissions
    if check_permissions_assessment(assessment, request.user) == 0:
        raise PermissionDenied("You do not have permissions to this assessment.")

    # get all attempts by score
    all_attempts = AssessmentAttempt.objects.filter(assessment__id=assessment_id,
                                                    time_submitted__isnull=False).prefetch_related("candidate")

    # create the HttpResponse object with the appropriate CSV header.
    filename = slugify(f"{assessment.course.code}_{assessment.name}_{timezone.now().strftime('%Y%m%d-%H%M')}")
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}.csv"'},
    )

    # columns: username, time_started, time_submitted, auto_submit, score
    writer = csv.writer(response)
    writer.writerow(["username", "score", "best_attempt", "time_started", "time_submitted", "auto_submit"])

    for attempt in all_attempts:
        writer.writerow([attempt.candidate.username,
                         attempt.score,
                         'Y' if attempt.best_attempt else 'N',
                         attempt.time_started,
                         attempt.time_submitted,
                         'Y' if attempt.auto_submit else 'N'])

    return response
