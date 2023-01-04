from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from core.decorators import groups_allowed, UserGroup
from core.filters import CourseStudentFilter
from core.forms.course_management import CourseForm
from core.models import Course, User, CourseGroup
from core.views.utils import check_permissions_course


@login_required()
@groups_allowed(UserGroup.educator, UserGroup.lab_assistant)
def view_courses(request):
    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct().prefetch_related(
        'owner', 'maintainers')

    active_courses = courses.filter(active=True)
    inactive_courses = courses.filter(active=False)

    context = {
        "active_courses": active_courses,
        "inactive_course": inactive_courses,
        "courses": courses
    }
    return render(request, 'course_management/courses.html', context)


@login_required()
@groups_allowed(UserGroup.educator)
def create_course(request):
    year_now = datetime.today().year
    year_start = 2020
    years = []
    for y in range(year_start, year_now + 2):
        years.append((y, y))

    # initialize form
    form = CourseForm(years, initial={'year': year_now, 'active': True})

    # process POST request
    if request.method == 'POST':  # POST
        form = CourseForm(years, request.POST)
        if form.is_valid():
            created_course = form.save(commit=False)
            created_course.owner = request.user
            created_course.save()
            messages.success(request, "The course has been created!")
            return redirect('view-courses')

    context = {
        'form': form,
    }
    return render(request, 'course_management/create-course.html', context)


@login_required()
@groups_allowed(UserGroup.educator)
def update_course(request, course_id):
    year_now = datetime.today().year
    year_start = 2020
    years = []
    for y in range(year_start, year_now + 2):
        years.append((y, y))

    # get course object
    course = get_object_or_404(Course.objects.prefetch_related('owner', 'maintainers'), id=course_id)

    # check permissions of user (needs to be owner)
    if check_permissions_course(course, request.user) != 2:
        raise PermissionDenied("You do not have permissions to modify the course.")

    # initialize form with course instance
    form = CourseForm(years, instance=course)

    # process POST request
    if request.method == 'POST':
        form = CourseForm(years, request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "The course has been updated!")

            # redirect to where the user came from
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
@groups_allowed(UserGroup.educator, UserGroup.lab_assistant)
def course_details(request, course_id):
    # get course object
    course = get_object_or_404(Course.objects.prefetch_related('owner', 'maintainers', 'coursegroup_set'), id=course_id)

    # if no permissions, redirect back to course page
    if check_permissions_course(course, request.user) == 0:
        raise PermissionDenied("You do not have permissions to view the course.")

    # get a list of staff accounts (educator/lab_assistant/superuser role)
    staff = User.objects.filter(Q(groups__name__in=('educator', 'lab_assistant')) & ~Q(username=request.user.username))

    # get queryset of students who are enrolled in this course
    course_groups = course.coursegroup_set.all().order_by('name')
    all_students = User.objects.filter(enrolled_groups__course=course) \
                                .prefetch_related('enrolled_groups', 'enrolled_groups__course') \
                                .order_by('username')
    students_filter = CourseStudentFilter(course_groups, request.GET, queryset=all_students)

    # paginate results
    paginator = Paginator(students_filter.qs, 15)
    page_num = request.GET.get('page', 1)
    try:
        students = paginator.page(page_num)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    context = {
        "course": course,
        "staff": staff,
        "students_filter": students_filter,
        "students": students,
    }

    return render(request, 'course_management/course-details.html', context)


@login_required()
@groups_allowed(UserGroup.educator, UserGroup.lab_assistant)
def remove_student(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        student_id = request.POST.get("student_id")

        # get course object
        course = Course.objects.filter(id=course_id).prefetch_related('owner', 'maintainers').first()
        if not course:
            context = {
                "result": "error",
                "msg": "The selected course does not exist."
            }
            return JsonResponse(context, status=200)

        # check if user has permissions for this course
        if check_permissions_course(course, request.user) == 0:
            context = {
                "result": "error",
                "msg": "You do not have permissions for this course."
            }
            return JsonResponse(context, status=200)

        # if no students selected
        if not student_id:
            context = {
                "result": "error",
                "msg": "No student selected."
            }
            return JsonResponse(context, status=200)

        # ensure student is enrolled in this course
        course_group = CourseGroup.objects.filter(course=course, students=student_id).first()
        if not course_group:
            context = {
                "result": "error",
                "msg": "The student is not enrolled in this course."
            }
            return JsonResponse(context, status=200)

        # remove the student
        course_group.students.remove(student_id)

        # result
        context = {
            "result": "success",
            "msg": "Student successfully removed!"
        }
        return JsonResponse(context, status=200)


@login_required()
@groups_allowed(UserGroup.educator)
def update_course_maintainer(request):
    """
    Function to add a maintainer to a course.
    Front-end does not display error messages for this feature, thus only the result of the operation is returned.
    """
    if request.method == "POST":
        # default error response
        error_context = {"result": "error", }

        # get params
        course_id = request.POST.get("course_id")
        maintainer_id = request.POST.get("maintainer_id")
        action = request.POST.get("action")

        # missing params
        if course_id is None or maintainer_id is None or action is None:
            return JsonResponse(error_context, status=200)

        # get course object
        course = Course.objects.filter(id=course_id).prefetch_related('owner', 'maintainers').first()

        # course not found
        if not course:
            return JsonResponse(error_context, status=200)

        # check if user has permissions for this course
        if check_permissions_course(course, request.user) != 2:
            return JsonResponse(error_context, status=200)

        # get maintainer object
        maintainer = User.objects.filter(id=maintainer_id).first()

        # if maintainer not found
        if not maintainer:
            return JsonResponse(error_context, status=200)

        # add maintainer to course
        if action == "add":
            course.maintainers.add(maintainer)
        elif action == "remove":
            course.maintainers.remove(maintainer)
        else:
            return JsonResponse(error_context, status=200)

        # return success
        return JsonResponse({"result": "success"}, status=200)


@login_required()
@groups_allowed(UserGroup.educator, UserGroup.lab_assistant)
def reset_student_password(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        student_id = request.POST.get("student_id")

        # get course
        course = Course.objects.filter(id=course_id).first()

        if not course:
            context = {
                "result": "error",
                "msg": "The course does not exist."
            }
            return JsonResponse(context, status=200)

        # check if user has permissions for this course
        if check_permissions_course(course, request.user) == 0:
            context = {
                "result": "error",
                "msg": "You do not have permissions for this course."
            }
            return JsonResponse(context, status=200)

        # check if student is even in the course
        if not CourseGroup.objects.filter(course=course, students=student_id).exists():
            context = {
                "result": "error",
                "msg": "Student does not exist in the course."
            }
            return JsonResponse(context, status=200)

        # get student and reset password
        student = User.objects.filter(id=student_id).first()
        student.password = make_password(settings.DEFAULT_STUDENT_PASSWORD)
        student.save()

        context = {
            "result": "success",
            "msg": f"Password successfully reset for {student.username}."
        }

        return JsonResponse(context, status=200)
