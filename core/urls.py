from django.urls import path

from .views import auth, user_management, dashboards, course_management, question_banks, code_questions, assessments, attempts

urlpatterns = [
    # global auth
    path('login/', auth.Login.as_view(), name='login'),
    path('logout/', auth.Logout.as_view(), name='logout'),

    # dashboards
    path('dashboard/students/', dashboards.dashboard_students, name='dashboard-students'),
    path('dashboard/educators/', dashboards.dashboard_educators, name='dashboard-educators'),
    path('dashboard/labassistants/', dashboards.dashboard_lab_assistants, name='dashboard-lab-assistants'),
    path('dashboard/', dashboards.dashboard, name='dashboard'),
    path('', dashboards.dashboard, name='dashboard'),

    # create student
    path('enrol-students/', user_management.enrol_students, name='enrol-students'),
    path('api/enrol-students-bulk/', user_management.enrol_students_bulk, name='enrol-students-bulk'),  # ajax

    # course management
    path('courses/', course_management.view_courses, name='view-courses'),
    path('courses/create/', course_management.create_course, name='create-course'),
    path('courses/update/<int:course_id>/', course_management.update_course, name='update-course'),
    path('courses/details/<int:course_id>/', course_management.course_details, name='course-details'),
    path('api/remove-student-from-course/', course_management.remove_student, name='remove-student-from-course'),  # ajax
    path('api/add-students-to-course/', course_management.add_students, name='add-students-to-course'),  # ajax
    path('api/get-course-students/', course_management.get_course_students, name='get-course-students'),  # ajax
    path('api/update-course-maintainer/', course_management.update_course_maintainer, name='update-course-maintainer'),  # ajax

    # question banks
    path('qb/', question_banks.view_question_banks, name='view-question-banks'),
    path('qb/create/', question_banks.create_question_bank, name='create-question-bank'),
    path('qb/update/<int:question_bank_id>/', question_banks.update_question_bank, name='update-question-bank'),
    path('qb/details/<int:question_bank_id>/', question_banks.question_bank_details, name='question-bank-details'),
    path('api/update-qb-shared-with/', question_banks.update_qb_shared_with, name='update-qb-shared-with'),  # ajax
    path('api/delete-code-question/', question_banks.delete_code_question, name='delete-code-question'),  # ajax

    # code questions
    path('code-question/create/<str:parent>/<int:parent_id>/', code_questions.create_code_question, name='create-code-question'),  # step 1
    path('code-question/<int:code_question_id>/update-test-cases/', code_questions.update_test_cases, name='update-test-cases'),  # step 2
    path('code-question/<int:code_question_id>/update-languages/', code_questions.update_languages, name='update-languages'),  # step 3
    path('code-question/update/<int:code_question_id>/', code_questions.update_code_question, name='update-code-question'),

    # assessments
    path('assessment/create/', assessments.create_assessment, name='create-assessment'),
    path('assessment/update/<int:assessment_id>/', assessments.update_assessment, name='update-assessment'),
    path('assessment/details/<int:assessment_id>/', assessments.assessment_details, name='assessment-details'),
    path('api/add-code-question-to-assessment/', assessments.add_code_question_to_assessment, name='add-code-question-to-assessment'),
    path('api/get-code-questions-questions/', assessments.get_code_questions, name='get-code-questions'),  # ajax

    # taking assessments (attempts)
    path('assessment/landing/<int:assessment_id>/', attempts.assessment_landing, name='assessment-landing'),
    path('assessment/enter/<int:assessment_id>/', attempts.enter_assessment, name='enter-assessment'),
    path('attempt/<int:assessment_attempt_id>/question/<int:question_index>/', attempts.attempt_question, name='attempt-question'),

    # code question attempts
    path('api/submit-single-test-case/<int:test_case_id>/', attempts.submit_single_test_case, name='submit-single-test-case'),  # ajax
    path('api/get-tc-details/', attempts.get_tc_details, name='get-tc-details'),  # ajax


]
