from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Assessment, AssessmentAttempt


@login_required()
def assessment_landing(request, assessment_id):
    """
    Landing page for a candidate taking an Assessment
    Displays the various information about an assessment
    """
    # get assessment object
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # check if user is enrolled into the course
    if not assessment.course.coursegroup_set.filter(students=request.user).exists():
        messages.warning(request, "You do not have permissions to view this assessment.")
        return redirect('dashboard')

    # check for incomplete attempts
    incomplete_attempt = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user, time_submitted=None)

    # check if there are any attempts remaining
    attempt_count = AssessmentAttempt.objects.filter(assessment=assessment, candidate=request.user).count()
    no_more_attempts = False if assessment.num_attempts == 0 else attempt_count >= assessment.num_attempts

    # context
    context = {
        'assessment': assessment,
        'attempt_count': attempt_count,
        'incomplete_attempt': incomplete_attempt,
        'no_more_attempts': no_more_attempts,
    }

    return render(request, 'attempts/assessment-landing.html', context)
