from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import User, Course, CourseGroup, QuestionBank, CodeQuestion, Assessment, TestCase, Language, CodeSnippet, CodeTemplate, Tag


class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'year', 'semester', 'owner', 'active')


class CourseGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'course', 'students_enrolled')


class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'owner', 'private')


class CodeQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'question_bank', 'assessment')


class LanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'judge_language_id')


class CodeTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'language')


class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'course', 'time_start', 'time_end', 'duration', 'num_attempts')


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


admin.site.register(User, UserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseGroup, CourseGroupAdmin)
admin.site.register(QuestionBank, QuestionBankAdmin)
admin.site.register(CodeQuestion, CodeQuestionAdmin)
admin.site.register(TestCase)
admin.site.register(Language)
admin.site.register(CodeSnippet)
admin.site.register(CodeTemplate, CodeTemplateAdmin)
admin.site.register(Assessment, AssessmentAdmin)
admin.site.register(Tag, TagAdmin)

