from django.contrib import admin
from .models import AcademicCourse, Subject, Course, Question, Result, ExamSession, ProctoringAlert

@admin.register(AcademicCourse)
class AcademicCourseAdmin(admin.ModelAdmin):
    list_display = ['code','name','created_at']
    search_fields = ['name','code']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code','name','academic_course']
    list_filter  = ['academic_course']
    search_fields = ['name','code']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_name','subject','duration_minutes','is_active','randomize_questions']
    list_filter  = ['is_active']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question','course','marks','answer']
    list_filter  = ['course']

@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ['student','course','status','started_at','expires_at','tab_switch_count','face_missing_count']
    list_filter  = ['status']
    readonly_fields = ['session_token','question_order','answers']

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student','exam','marks','total_marks','percentage','grade','auto_submitted','date']
    list_filter  = ['exam','auto_submitted']

@admin.register(ProctoringAlert)
class ProctoringAlertAdmin(admin.ModelAdmin):
    list_display = ['student','alert_type','course','timestamp']
    list_filter  = ['alert_type']
