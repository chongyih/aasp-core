from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from core.forms.course_management import CourseForm
from core.models import Course, User


@login_required()
def view_courses(request):
    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct()

    context = {
        "courses": courses
    }
    return render(request, 'course_management/courses.html', context)


@login_required()
def create_course(request):
    year_start = datetime.today().year - 1
    years = []
    for y in range(year_start, year_start + 5):
        years.append((y, y))

    # initialize form
    form = CourseForm(years)

    # process POST request
    if request.method == 'POST':  # POST
        form = CourseForm(years, request.POST)
        if form.is_valid():
            created_course = form.save(commit=False)
            created_course.owner = request.user
            created_course.save()
            messages.success(request, "The course has been created! ✅")
            # mytodo: change to course details page
            return redirect('dashboard')

    context = {
        'form': form,
    }
    return render(request, 'course_management/create-course.html', context)


class HTTPResponseRedirect:
    pass


def update_course(request, course_id):
    current_year = datetime.today().year
    years = []
    for y in range(2020, current_year + 5):
        years.append((y, y))

    # get course object
    course = get_object_or_404(Course, id=course_id)

    # initialize form with course instance
    form = CourseForm(years, instance=course)

    # process POST request
    if request.method == 'POST':
        form = CourseForm(years, request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "The course has been updated! ✅")

            # redirect to where user the came from
            next_url = request.GET.get("next")
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                return redirect('view-courses')

    context = {
        'form': form,
    }
    return render(request, 'course_management/update-course.html', context)


@login_required()
def course_details(request, course_id):
    # get course object
    course = get_object_or_404(Course, id=course_id)

    # if no permissions, redirect back to courses page
    if course.owner != request.user and request.user not in course.maintainers.all():
        messages.warning(request, "You do not have permissions to view that course.")
        return redirect('view-courses')

    context = {
        "course": course
    }

    return render(request, 'course_management/course-details.html', context)


@login_required()
def remove_students(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        student_ids = request.POST.get("student_ids")

        # get course object
        course = Course.objects.filter(id=course_id).first()
        if not course:
            context = {
                "result": "error",
                "msg": "The selected course does not exist."
            }
            return JsonResponse(context, status=200)

        # check if user has permissions for this course
        if course.owner != request.user and request.user not in course.maintainers.all():
            context = {
                "result": "error",
                "msg": "You do not have permissions for this course."
            }
            return JsonResponse(context, status=200)

        if student_ids is not None:
            student_ids = student_ids.split(",")

        # if no students selected
        if not student_ids:
            context = {
                "result": "error",
                "msg": "No students selected."
            }
            return JsonResponse(context, status=200)

        # remove students from course
        course.students.remove(*student_ids)

        # result
        context = {
            "result": "success",
            "msg": "Students successfully removed!"
        }
        return JsonResponse(context, status=200)


@login_required()
def add_students(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        usernames = request.POST.get("usernames")

        # get course object
        course = Course.objects.filter(id=course_id).first()
        if not course:
            context = {
                "result": "error",
                "msg": "The selected course does not exist."
            }
            return JsonResponse(context, status=200)

        # check if user has permissions for this course
        if course.owner != request.user and request.user not in course.maintainers.all():
            context = {
                "result": "error",
                "msg": "You do not have permissions for this course."
            }
            return JsonResponse(context, status=200)

        if usernames is not None:
            usernames = usernames.strip().splitlines()

        # if no usernames entered
        if not usernames:
            context = {
                "result": "error",
                "msg": "No usernames selected."
            }
            return JsonResponse(context, status=200)

        # check which usernames exist, which does not...?

