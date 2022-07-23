from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from core.models import Assessment, AssessmentAttempt


@login_required()
def assessment_report(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)

    best_attempts = AssessmentAttempt.objects.filter(assessment=assessment, best_attempt=True).order_by('-score')
    ongoing_ungraded_attempts = AssessmentAttempt.objects.filter(Q(assessment=assessment, time_submitted__isnull=True) | Q(assessment=assessment, time_submitted__isnull=False, score__isnull=True))

    print("best_attempts:", best_attempts)
    print("ongoing_ungraded_attempts:", ongoing_ungraded_attempts)

    context = {
        "assessment": assessment,
        "best_attempts": best_attempts,
        "ongoing_ungraded_attempts": ongoing_ungraded_attempts,
    }

    return render(request, 'reports/assessment-report.html', context)


@login_required()
def get_candidate_attempts(request, assessment_id):
    # get candidate_id
    candidate_id = request.GET.get('candidate_id')
    if not candidate_id:
        return JsonResponse({"result": "error"}, status=200)

    # get assessment attempts
    assessment_attempts = AssessmentAttempt.objects.filter(assessment__id=assessment_id, candidate__id=candidate_id)\
        .values('id', 'time_started', 'time_submitted', 'auto_submit', 'score', 'best_attempt').order_by('id')

    # prepare context
    context = {
        "result": "success",
        "assessment_attempts": list(assessment_attempts)
    }
    return JsonResponse(context, status=200)
