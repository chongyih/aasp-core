from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from core.forms.user_management import StudentCreationForm
from core.models import User, Course
from core.views.utils import clean_csv


@login_required()
def create_student(request):
    """
    Student creation page
    Single-user form submission handled here, bulk creation handled with create_student_bulk()
    """

    # retrieve courses for this user
    courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct()

    if request.method == 'POST':  # POST
        form = StudentCreationForm(courses, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "The user has been created! ✅")
            return redirect('create-student')
    else:  # GET
        form = StudentCreationForm(courses=courses)

    context = {
        'form': form
    }

    return render(request, 'user_management/create-student.html', context)


@login_required()
def create_student_bulk(request):
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
        if course.get_permissions(request.user) == 0:
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

            # ensure users don't exist in database yet (by checking username)
            # get conflicted username values
            existing_users = list(User.objects.filter(username__in=[row[2] for row in cleaned_rows]))
            existing_usernames = [u.username for u in existing_users]

            # generate User objects from contents of the csv file
            user_objects = []  # user accounts that will be created, and added to course
            conflicted_rows = []  # user accounts that will not be created, but will be added course
            for row in cleaned_rows:
                # create only if fields are not conflicted
                if row[2] not in existing_usernames:
                    user_objects.append(
                        User(first_name=row[0], last_name=row[1], email=f"{row[2]}@E.NTU.EDU.SG", username=row[2],
                             password=make_password(settings.DEFAULT_STUDENT_PASSWORD)))
                else:
                    conflicted_rows.append(row)

            print("removed_rows:", removed_rows)
            print("conflicted_rows:", conflicted_rows)
            print("number added:", len(user_objects))

            # bulk create with database
            # bulk_create returns all objects that was given to it when ignore_conflicts=True, even those that were not added to the database
            created_users = User.objects.bulk_create(user_objects, ignore_conflicts=False)

            # add to student group
            Group.objects.get(name="student").user_set.add(*created_users)

            # add to course
            if course_id:
                course.students.add(*(created_users+existing_users))

            # success message
            n = len(created_users)
            if n == 0:
                msg = "No accounts were created. Refer to the section below for more details."
            else:
                if len(conflicted_rows) == 0 and len(removed_rows) == 0:
                    msg = f"Success! {n} student account(s) were created."
                else:
                    msg = f"Success! {n} student account(s) were created, with some rows ignored (refer to the section below for more details)."

            # result
            context = {
                "result": "success",
                "msg": msg,
                "removed_rows": removed_rows,
                "conflicted_rows": conflicted_rows,
            }

            return JsonResponse(context, status=200)

        except Exception as e:
            print(e)
            return JsonResponse({"result": "error", "msg": "Something went wrong while processing your file."}, status=200)
