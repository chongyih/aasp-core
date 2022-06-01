from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from core.filters import CourseStudentFilter
from core.forms.course_management import CourseForm
from core.models import Course, User, CourseGroup
from core.views.utils import check_permissions


@login_required()
def view_courses(request):
    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct().prefetch_related('owner', 'maintainers')

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
            return redirect('view-courses')

    context = {
        'form': form,
    }
    return render(request, 'course_management/create-course.html', context)


@login_required()
def update_course(request, course_id):
    current_year = datetime.today().year
    years = []
    for y in range(2020, current_year + 5):
        years.append((y, y))

    # get course object
    course = get_object_or_404(Course.objects.prefetch_related('owner', 'maintainers'), id=course_id)

    # check permissions of user (needs to be owner)
    if check_permissions(course, request.user) != 2:
        messages.warning(request, "You do not have permissions to update the course.")
        return redirect('view-courses')

    # initialize form with course instance
    form = CourseForm(years, instance=course)

    # process POST request
    if request.method == 'POST':
        form = CourseForm(years, request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "The course has been updated! ✅")

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
def course_details(request, course_id):
    # get course object
    course = get_object_or_404(Course.objects.prefetch_related('owner', 'maintainers', 'coursegroup_set'), id=course_id)

    # if no permissions, redirect back to course page
    if check_permissions(course, request.user) == 0:
        messages.warning(request, "You do not have permissions to view that course.")
        return redirect('view-courses')

    # get a list of staff accounts (educator/lab_assistant/superuser role)
    staff = User.objects.filter(Q(groups__name__in=('educator', 'lab_assistant')) | Q(is_superuser=True))

    # get queryset of students who are enrolled in this course
    course_groups = course.coursegroup_set.all()
    all_students = User.objects.filter(enrolled_groups__course=course).prefetch_related('enrolled_groups', 'enrolled_groups__course').order_by(
        'username')
    students_filter = CourseStudentFilter(course_groups, request.GET, queryset=all_students)

    context = {
        "course": course,
        "staff": staff,
        "students_filter": students_filter,
    }

    return render(request, 'course_management/course-details.html', context)


@login_required()
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
        if check_permissions(course, request.user) == 0:
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


@login_required()  # not used
def add_students(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        usernames = request.POST.get("usernames")

        # get course object
        course = Course.objects.filter(id=course_id).prefetch_related('owner', 'maintainers').first()
        if not course:
            context = {
                "result": "error",
                "msg": "The selected course does not exist."
            }
            return JsonResponse(context, status=200)

        # check if user has permissions for this course
        if check_permissions(course, request.user) == 0:
            context = {
                "result": "error",
                "msg": "You do not have permissions for this course."
            }
            return JsonResponse(context, status=200)

        if usernames is not None:
            usernames = usernames.upper().strip().splitlines()

        # remove duplicates by converting to set
        usernames = set(usernames)

        # if no usernames entered
        if not usernames:
            context = {
                "result": "error",
                "msg": "No usernames selected."
            }
            return JsonResponse(context, status=200)

        # check which usernames exist, which does not...?
        user_search = User.objects.in_bulk(usernames, field_name="username")

        # retrieve user ids from the search results
        student_ids = [user.id for user in user_search.values()]

        # add these IDs to the course
        course.students.add(*student_ids)

        # compute list of usernames that were not found
        not_found = list(set(usernames) - set(user_search.keys()))

        # success message
        n = len(student_ids)
        if n == 0:
            msg = "No students were added to the course. Refer to the section below for more details."
        else:
            if len(not_found) == 0:
                msg = f"{n} student(s) were successfully added to the course!"
            else:
                msg = f"{n} student(s) were successfully added to the course, with some rows ignored (refer to the section below for more details)."

        # result
        context = {
            "result": "success",
            "msg": msg,
            "not_found": not_found,
        }
        return JsonResponse(context, status=200)


@login_required()  # not used
def get_course_students(request):
    if request.method == "GET":
        course_id = request.GET.get("course_id")

        # get course object
        course = Course.objects.filter(id=course_id).prefetch_related('owner', 'maintainers').first()
        if not course:
            context = {
                "result": "error",
                "msg": "The course does not exist."
            }
            return JsonResponse(context, status=200)

        # check if user has permissions for this course
        if check_permissions(course, request.user) == 0:
            context = {
                "result": "error",
                "msg": "You do not have permissions for this course."
            }
            return JsonResponse(context, status=200)

        # get students
        students = list(course.students.all().values('id', 'username', 'first_name', 'last_name'))

        # get students
        return JsonResponse({"result": "success", "students": students}, status=200)


@login_required()
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
        if check_permissions(course, request.user) != 2:
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
