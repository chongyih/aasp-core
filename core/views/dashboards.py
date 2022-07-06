from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

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
    # retrieve all assessments for this user
    assessments = Assessment.objects.filter(course__coursegroup__students=request.user)
    context = {
        'assessments': assessments
    }
    return render(request, 'dashboards/students.html', context)


@login_required
@user_passes_test(is_educator, login_url='dashboard')
def dashboard_educators(request):
    user = request.user
    context = {}
    return render(request, 'dashboards/educators.html', context)


@login_required
@user_passes_test(is_lab_assistant, login_url='dashboard')
def dashboard_lab_assistants(request):
    user = request.user
    context = {}
    return render(request, 'dashboards/lab_assistants.html', context)
