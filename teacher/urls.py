from django.urls import path
from teacher import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('teacherclick', views.teacherclick_view, name='teacherclick'),
    path('teacherlogin', LoginView.as_view(template_name='teacher/teacherlogin.html'), name='teacherlogin'),
    path('teachersignup', views.teacher_signup_view, name='teachersignup'),
    path('teacher-dashboard', views.teacher_dashboard_view, name='teacher-dashboard'),

    # Academic hierarchy
    path('teacher-academic-course', views.teacher_academic_course_view, name='teacher-academic-course'),
    path('teacher-add-academic-course', views.teacher_add_academic_course_view, name='teacher-add-academic-course'),
    path('teacher-delete-academic-course/<int:pk>', views.teacher_delete_academic_course_view, name='teacher-delete-academic-course'),
    path('teacher-subject', views.teacher_subject_view, name='teacher-subject'),
    path('teacher-add-subject', views.teacher_add_subject_view, name='teacher-add-subject'),
    path('teacher-delete-subject/<int:pk>', views.teacher_delete_subject_view, name='teacher-delete-subject'),

    # Exams
    path('teacher-exam', views.teacher_exam_view, name='teacher-exam'),
    path('teacher-add-exam', views.teacher_add_exam_view, name='teacher-add-exam'),
    path('teacher-view-exam', views.teacher_view_exam_view, name='teacher-view-exam'),
    path('teacher-edit-exam/<int:pk>', views.teacher_edit_exam_view, name='teacher-edit-exam'),
    path('delete-exam/<int:pk>', views.delete_exam_view, name='delete-exam'),
    path('teacher-upload-quiz/<int:pk>', views.teacher_upload_quiz_view, name='teacher-upload-quiz'),
    path('teacher-upload-answer-key/<int:pk>', views.teacher_upload_answer_key_view, name='teacher-upload-answer-key'),

    # Questions
    path('teacher-question', views.teacher_question_view, name='teacher-question'),
    path('teacher-add-question', views.teacher_add_question_view, name='teacher-add-question'),
    path('teacher-view-question', views.teacher_view_question_view, name='teacher-view-question'),
    path('see-question/<int:pk>', views.see_question_view, name='see-question'),
    path('remove-question/<int:pk>', views.remove_question_view, name='remove-question'),

    # Reports
    path('teacher-view-results', views.teacher_view_results_view, name='teacher-view-results'),
    path('teacher-proctoring', views.teacher_proctoring_view, name='teacher-proctoring'),
]
