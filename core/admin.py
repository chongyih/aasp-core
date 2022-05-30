from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import User, Course, CourseGroup, QuestionBank

# Register your models here.

admin.site.register(User, UserAdmin)
admin.site.register(Course)
admin.site.register(CourseGroup)
admin.site.register(QuestionBank)
