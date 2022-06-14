from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.forms.assessments import AssessmentForm
from core.models import Course
from core.views.utils import check_permissions


def create_assessment(request):
    # get course_id if exists
    course_id = request.GET.get('course_id')

    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct().prefetch_related('owner', 'maintainers')

    # form
    form = AssessmentForm(courses=courses, initial={'course': course_id})

    # process POST request
    if request.method == "POST":
        form = AssessmentForm(request.POST, courses=courses)

        # check permissions before saving form
        # if check_permissions(course, request) == 0:
        #     messages.success(request, "You do not have permissions for this course.")
        #     return redirect('view-courses')

    context = {
        'form': form,

    }

    return render(request, 'assessments/create-assessment.html', context)