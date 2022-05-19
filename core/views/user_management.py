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
    print(context)
    return render(request, 'user_management/create-student.html', context)


@login_required()
def create_student_bulk(request):
    if request.method == "POST":
        # retrieve courses for this user
        courses = Course.objects.filter(Q(owner=request.user) | Q(maintainers=request.user)).distinct()

        # retrieve selected course from the request if exist
        course_id = request.POST.get("course")

        # if selected, ensure user has permissions
        if course_id:
            if not courses.filter(id=course_id).exists():
                context = {
                    "result": "error",
                    "msg": "Invalid course selected!"
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
            csv_rows = file.read().decode('utf-8').splitlines()

            # clean the csv file
            cleaned_rows, removed_rows = clean_csv(csv_rows)

            # ensure users don't exist in database yet (by checking fields with UNIQUE constraint)
            # 1. get conflicted identification values
            conflict_identification = User.objects.filter(identification__in=[row[2] for row in cleaned_rows])
            conflict_identification = [u.identification for u in conflict_identification]

            # 2. get conflicted email values
            conflict_email = User.objects.filter(email__in=[row[3] for row in cleaned_rows])
            conflict_email = [u.email for u in conflict_email]

            # 3. get conflicted username values
            conflict_username = User.objects.filter(username__in=[row[4] for row in cleaned_rows])
            conflict_username = [u.email for u in conflict_username]

            # generate User objects from contents of the csv file
            default_password = make_password("password123!")
            user_accounts = []
            conflicted_rows = []
            for row in cleaned_rows:
                # create only if fields are not conflicted
                if row[2] not in conflict_identification and row[3] not in conflict_email and row[4] not in conflict_username:
                    user_accounts.append(
                        User(first_name=row[0], last_name=row[1], identification=row[2], email=row[3], username=row[4], password=default_password))
                else:
                    conflicted_rows.append(row)

            print("removed_rows:", removed_rows)
            print("cleaned_rows:", cleaned_rows)
            print("conflicted_rows:", conflicted_rows)
            print("number added:", len(user_accounts))

            # bulk create with database
            # bulk_create returns all objects that was given to it when ignore_conflicts=True, even those that were not added to the database
            created_accounts = User.objects.bulk_create(user_accounts, ignore_conflicts=False)

            # add to student group
            Group.objects.get(name="student").user_set.add(*created_accounts)

            # success message
            if len(created_accounts) == 0:
                msg = "No accounts were created. Refer to the section below for more details."
            else:
                if len(conflicted_rows) == 0 and len(removed_rows) == 0:
                    msg = f"Success! {len(created_accounts)} student account(s) were created."
                else:
                    msg = f"Success! {len(created_accounts)} student account(s) were created, with some rows ignored (refer to the section below for more details)."

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
