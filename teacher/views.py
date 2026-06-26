from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.db.models import Count
from django.contrib import messages

from . import forms, models
from exam import models as QMODEL
from exam import forms as QFORM
from student import models as SMODEL
from exam.services.question_parser import QuestionParserFactory, save_parsed_questions


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()


def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'teacher/teacherclick.html')


def teacher_signup_view(request):
    userForm = forms.TeacherUserForm()
    teacherForm = forms.TeacherForm()
    if request.method == 'POST':
        userForm = forms.TeacherUserForm(request.POST)
        teacherForm = forms.TeacherForm(request.POST, request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            teacher = teacherForm.save(commit=False)
            teacher.user = user
            teacher.save()
            Group.objects.get_or_create(name='TEACHER')[0].user_set.add(user)
            messages.success(request, 'Registration submitted! Await admin approval.')
            return HttpResponseRedirect('teacherlogin')
    return render(request, 'teacher/teachersignup.html', {
        'userForm': userForm, 'teacherForm': teacherForm
    })


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    ctx = {
        'total_course': QMODEL.Course.objects.count(),
        'total_question': QMODEL.Question.objects.count(),
        'total_student': SMODEL.Student.objects.count(),
        'total_academic': QMODEL.AcademicCourse.objects.count(),
        'total_subjects': QMODEL.Subject.objects.count(),
        'recent_exams': QMODEL.Course.objects.select_related('subject').order_by('-created_at')[:5],
    }
    return render(request, 'teacher/teacher_dashboard.html', ctx)


# ── Academic Course ──────────────────────────────────────────────────────────

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_academic_course_view(request):
    courses = QMODEL.AcademicCourse.objects.annotate(sub_count=Count('subjects')).all()
    return render(request, 'teacher/teacher_academic_course.html', {'courses': courses})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_academic_course_view(request):
    form = QFORM.AcademicCourseForm()
    if request.method == 'POST':
        form = QFORM.AcademicCourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Academic course added.')
            return redirect('teacher-academic-course')
    return render(request, 'teacher/teacher_add_academic_course.html', {'form': form})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_delete_academic_course_view(request, pk):
    get_object_or_404(QMODEL.AcademicCourse, id=pk).delete()
    messages.success(request, 'Academic course deleted.')
    return redirect('teacher-academic-course')


# ── Subject ──────────────────────────────────────────────────────────────────

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_subject_view(request):
    subjects = QMODEL.Subject.objects.select_related('academic_course').all()
    return render(request, 'teacher/teacher_subject.html', {'subjects': subjects})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_subject_view(request):
    form = QFORM.SubjectForm()
    if request.method == 'POST':
        form = QFORM.SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added.')
            return redirect('teacher-subject')
    return render(request, 'teacher/teacher_add_subject.html', {'form': form})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_delete_subject_view(request, pk):
    get_object_or_404(QMODEL.Subject, id=pk).delete()
    messages.success(request, 'Subject deleted.')
    return redirect('teacher-subject')


# ── Exam / Quiz ──────────────────────────────────────────────────────────────

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    return render(request, 'teacher/teacher_exam.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_exam_view(request):
    courseForm = QFORM.CourseForm()
    if request.method == 'POST':
        courseForm = QFORM.CourseForm(request.POST)
        if courseForm.is_valid():
            courseForm.save()
            messages.success(request, 'Exam created successfully.')
        else:
            messages.error(request, 'Please fix the errors below.')
        return redirect('teacher-view-exam')
    return render(request, 'teacher/teacher_add_exam.html', {'courseForm': courseForm})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_exam_view(request):
    courses = QMODEL.Course.objects.select_related('subject__academic_course').annotate(
        q_count=Count('questions')
    ).order_by('-created_at')
    return render(request, 'teacher/teacher_view_exam.html', {'courses': courses})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_edit_exam_view(request, pk):
    course = get_object_or_404(QMODEL.Course, id=pk)
    courseForm = QFORM.CourseForm(instance=course)
    if request.method == 'POST':
        courseForm = QFORM.CourseForm(request.POST, instance=course)
        if courseForm.is_valid():
            courseForm.save()
            messages.success(request, 'Exam updated.')
            return redirect('teacher-view-exam')
    return render(request, 'teacher/teacher_edit_exam.html', {'courseForm': courseForm, 'course': course})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def delete_exam_view(request, pk):
    course = get_object_or_404(QMODEL.Course, id=pk)
    # Only delete if no results recorded
    if QMODEL.Result.objects.filter(exam=course).exists():
        messages.error(request, 'Cannot delete: exam already has student results.')
    else:
        course.delete()
        messages.success(request, 'Exam deleted.')
    return redirect('teacher-view-exam')


# ── Quiz File Upload ──────────────────────────────────────────────────────────

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_upload_quiz_view(request, pk):
    course = get_object_or_404(QMODEL.Course, id=pk)
    uploadForm = QFORM.QuizUploadForm(instance=course)
    parse_result = None
    if request.method == 'POST':
        uploadForm = QFORM.QuizUploadForm(request.POST, request.FILES, instance=course)
        if uploadForm.is_valid():
            course = uploadForm.save()
            messages.success(request, 'File uploaded.')
            # Attempt to parse uploaded quiz file
            if course.quiz_file:
                try:
                    parsed = QuestionParserFactory.parse_file(course.quiz_file)
                    parse_result = save_parsed_questions(parsed, course)
                    if parse_result['saved']:
                        messages.success(request, f"{parse_result['saved']} questions imported automatically.")
                    if parse_result['errors']:
                        messages.warning(request, f"{parse_result['skipped']} rows skipped.")
                except Exception as e:
                    messages.info(request, f'File saved. Manual question entry needed ({e}).')
    return render(request, 'teacher/teacher_upload_quiz.html', {
        'course': course, 'uploadForm': uploadForm, 'parse_result': parse_result
    })


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_upload_answer_key_view(request, pk):
    course = get_object_or_404(QMODEL.Course, id=pk)
    if request.method == 'POST' and request.FILES.get('answer_key_file'):
        course.answer_key_file = request.FILES['answer_key_file']
        course.save()
        messages.success(request, 'Answer key uploaded.')
        return redirect('teacher-view-exam')
    return render(request, 'teacher/teacher_upload_answer_key.html', {'course': course})


# ── Questions ─────────────────────────────────────────────────────────────────

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_question_view(request):
    return render(request, 'teacher/teacher_question.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    questionForm = QFORM.QuestionForm()
    courses = QMODEL.Course.objects.all()
    if request.method == 'POST':
        questionForm = QFORM.QuestionForm(request.POST)
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            course = get_object_or_404(QMODEL.Course, id=request.POST.get('courseID'))
            question.course = course
            question.save()
            messages.success(request, 'Question added.')
        return redirect('teacher-view-question')
    return render(request, 'teacher/teacher_add_question.html', {
        'questionForm': questionForm, 'courses': courses
    })


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    courses = QMODEL.Course.objects.annotate(q_count=Count('questions')).all()
    return render(request, 'teacher/teacher_view_question.html', {'courses': courses})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request, pk):
    questions = QMODEL.Question.objects.filter(course_id=pk)
    course = get_object_or_404(QMODEL.Course, id=pk)
    return render(request, 'teacher/see_question.html', {'questions': questions, 'course': course})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request, pk):
    get_object_or_404(QMODEL.Question, id=pk).delete()
    messages.success(request, 'Question removed.')
    return redirect('teacher-view-question')


# ── Results / Reports ─────────────────────────────────────────────────────────

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_results_view(request):
    results = QMODEL.Result.objects.select_related('student__user', 'exam').order_by('-date')
    return render(request, 'teacher/teacher_view_results.html', {'results': results})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_proctoring_view(request):
    alerts = QMODEL.ProctoringAlert.objects.select_related('student__user', 'course').all()[:300]
    return render(request, 'teacher/teacher_proctoring.html', {'alerts': alerts})
