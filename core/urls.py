from django.urls import path

from .views import auth, user_management, dashboards, course_management

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
    path('create-student/', user_management.create_student, name='create-student'),
    path('api/create_student_bulk/', user_management.create_student_bulk, name='create-student-bulk'),  # ajax

    # course management
    path('courses/', course_management.view_courses, name='view-courses'),
    path('courses/create/', course_management.create_course, name='create-course'),
    path('courses/update/<int:course_id>/', course_management.update_course, name='update-course'),
    path('courses/details/<int:course_id>/', course_management.course_details, name='course-details'),
    path('api/remove-students-from-course/', course_management.remove_students, name='remove-students-from-course'),  # ajax
    path('api/add-students-to-course/', course_management.add_students, name='add-students-to-course'),  # ajax




]
