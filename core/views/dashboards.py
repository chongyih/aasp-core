from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone

from core.models import Course, CourseGroup, Assessment
from core.views.utils import is_student, is_educator, is_lab_assistant


@login_required
def dashboard(request):
    """
    redirects a logged-in user to the correct dashboard
    """
    if request.user.is_superuser:
        return redirect('dashboard-educators')
    elif request.user.groups.filter(name='student').exists():
        return redirect('dashboard-students')
    elif request.user.groups.filter(name='educator').exists():
        return redirect('dashboard-educators')
    elif request.user.groups.filter(name='lab_assistant').exists():
        return redirect('dashboard-lab-assistants')


@login_required
@user_passes_test(is_student, login_url='dashboard')
def dashboard_students(request):
    # courses count
    courses_count = Course.objects.filter(coursegroup__students=request.user, active=True).count()

    # retrieve all assessments for this user
    assessments = Assessment.objects.filter(course__coursegroup__students=request.user, published=True, deleted=False)

    # active
    active_assessments = [a for a in assessments if a.status == "Active"]

    # upcoming
    upcoming_assessments = [a for a in assessments if a.status == "Upcoming"]

    # past
    past_assessments = [a for a in assessments if a.status == "Ended"]

    context = {
        'courses_count': courses_count,
        'assessments': assessments,
        'active_assessments': active_assessments,
        'upcoming_assessments': upcoming_assessments,
        'past_assessments': past_assessments,
    }
    return render(request, 'dashboards/students.html', context)


@login_required
@user_passes_test(is_educator, login_url='dashboard')
def dashboard_educators(request):
    # get active courses
    courses = Course.objects.filter(
        Q(owner=request.user) |
        Q(maintainers=request.user)
    ).filter(active=True).distinct()

    # retrieve all assessments for this user
    assessments = Assessment.objects.filter(course__in=courses, published=True, deleted=False)

    active_count = 0
    upcoming_count = 0
    past_count = 0

    for a in assessments:
        status = a.status
        if status == "Active":
            active_count += 1
        elif status == "Upcoming":
            upcoming_count += 1
        elif status == "Ended":
            past_count += 1

    # context
    context = {
        'courses': courses,
        'active_count': active_count,
        'upcoming_count': upcoming_count,
        'past_count': past_count,
    }
    return render(request, 'dashboards/educators.html', context)


@login_required
@user_passes_test(is_lab_assistant, login_url='dashboard')
def dashboard_lab_assistants(request):
    context = {}
    return render(request, 'dashboards/lab_assistants.html', context)
