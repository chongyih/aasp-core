from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.forms.user_management import StudentCreationForm
from core.models import User, Course, CourseGroup
from core.views.utils import clean_csv, check_permissions


@login_required()
def enrol_students(request):
    """
    Student enrolment page
    Single-user form submission handled here, bulk creation handled with create_student_bulk()
    """

    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct().prefetch_related('owner', 'maintainers')

    if request.method == 'POST':  # POST
        form = StudentCreationForm(courses, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "The user has been added to the Course! ✅")
            return redirect('enrol-students')
    else:  # GET
        form = StudentCreationForm(courses=courses)

    context = {
        'form': form
    }

    return render(request, 'user_management/enrol-student.html', context)


@login_required()
def enrol_students_bulk(request):
    if request.method == "POST":
        # retrieve selected course from the request if exist
        course_id = request.POST.get("course", None)

        if not course_id:
            context = {
                "result": "error",
                "msg": "Please select a course."
            }
            return JsonResponse(context, status=200)

        # get course object
        course = Course.objects.filter(id=course_id).first()

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

        # retrieve the file from the request
        file = request.FILES.get('file')

        # if no file received, return with error
        if not file:
            return JsonResponse({"result": "error", "msg": "No file was uploaded."}, status=200)

        # check if file is csv
        if not file.name.endswith('.csv'):
            return JsonResponse({"result": "error", "msg": "Only csv files are accepted!"}, status=200)

        # ensure file is <= 5MB
        if file.size >= 5242880:
            return JsonResponse({"result": "error", "msg": "The uploaded file is too large! (up to 5MB allowed)"}, status=200)

        # process uploaded file
        try:
            # decode uploaded file
            csv_rows = file.read().decode('utf-8').upper().splitlines()

            # clean the csv file (removes invalid/duplicated rows, and rows with conflicting usernames)
            cleaned_rows, removed_rows = clean_csv(csv_rows)

            # map course_group to students
            course_groups = {}
            for row in cleaned_rows:
                group = row[3]
                username = row[2]
                course_groups[group] = course_groups.get(group, [])
                course_groups[group].append(username)

            # ensure users don't exist in database yet (by checking username)
            # get conflicted username values
            existing_users = list(User.objects.filter(username__in=[row[2] for row in cleaned_rows]))
            existing_usernames = [u.username for u in existing_users]

            # generate User objects from contents of the csv file
            user_objects = []  # user accounts to be created
            default_password = make_password(settings.DEFAULT_STUDENT_PASSWORD)
            for row in cleaned_rows:
                # create only if account don't exist yet
                if row[2] not in existing_usernames:
                    user_objects.append(
                        User(first_name=row[0], last_name=row[1], email=f"{row[2]}@E.NTU.EDU.SG", username=row[2],
                             password=default_password))

            # bulk create with database
            created_users = User.objects.bulk_create(user_objects, ignore_conflicts=False)

            # add to student role group
            created_user_objects = User.objects.filter(username__in=[x.username for x in created_users])
            Group.objects.get(name="student").user_set.add(*created_user_objects)

            for k, v in course_groups.items():
                course_group, _ = CourseGroup.objects.get_or_create(course=course, name=k)
                course_group.students.add(*User.objects.filter(username__in=v))

            # success message
            msg = f"{len(created_users) + len(existing_users)} students enrolled successfully!"
            if len(removed_rows) != 0:
                msg += " Some rows were ignored, refer to the section below for more details."

            # result
            context = {
                "result": "success",
                "msg": msg,
                "removed_rows": removed_rows,
                "conflicted_rows": []
            }

            return JsonResponse(context, status=200)

        except Exception as e:
            print(e)
            return JsonResponse({"result": "error", "msg": "Something went wrong while processing your file."}, status=200)
