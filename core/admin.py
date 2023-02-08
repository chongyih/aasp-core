from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.models import User, Course, CourseGroup, QuestionBank, CodeQuestion, Assessment, TestCase, Language, CodeSnippet, CodeTemplate, Tag, \
    AssessmentAttempt, CodeQuestionAttempt, CodeQuestionSubmission, TestCaseAttempt, CandidateSnapshot


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_superuser", "session_key")
    readonly_fields = ("email", "session_key", "is_staff", "last_login", "date_joined")


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


class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'candidate')


class CodeQuestionAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'assessment_attempt', 'code_question', 'attempted')


class CodeQuestionSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cq_attempt', 'time_submitted', 'passed')


class TestCaseAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'cq_submission', 'test_case', 'token', 'status')


class CandidateSnapshotAdmin(admin.ModelAdmin):
    list_display = ('id', 'assessment_attempt', 'attempt_number', 'timestamp', 'faces_detected', 'image')


admin.site.register(User, CustomUserAdmin)
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
admin.site.register(AssessmentAttempt, AssessmentAttemptAdmin)
admin.site.register(CodeQuestionAttempt, CodeQuestionAttemptAdmin)
admin.site.register(CodeQuestionSubmission, CodeQuestionSubmissionAdmin)
admin.site.register(TestCaseAttempt, TestCaseAttemptAdmin)
admin.site.register(CandidateSnapshot, CandidateSnapshotAdmin)
