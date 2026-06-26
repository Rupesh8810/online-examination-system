from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Sum, Count
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

from . import forms, models
from teacher import models as TMODEL
from student import models as SMODEL
from teacher import forms as TFORM
from student import forms as SFORM


# ─── Helpers ────────────────────────────────────────────────────────────────

def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()


# ─── Home / Auth routing ─────────────────────────────────────────────────────

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'exam/index.html')


def afterlogin_view(request):
    if is_student(request.user):
        return redirect('student-dashboard')
    elif is_teacher(request.user):
        approval = TMODEL.Teacher.objects.filter(user_id=request.user.id, status=True).exists()
        if approval:
            return redirect('teacher-dashboard')
        else:
            return render(request, 'teacher/teacher_wait_for_approval.html')
    else:
        return redirect('admin-dashboard')


def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


def aboutus_view(request):
    return render(request, 'exam/aboutus.html')


def contactus_view(request):
    form = forms.ContactusForm()
    if request.method == 'POST':
        form = forms.ContactusForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['Email']
            name = form.cleaned_data['Name']
            message = form.cleaned_data['Message']
            try:
                send_mail(
                    f'{name} || {email}', message,
                    settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER,
                    fail_silently=False
                )
                return render(request, 'exam/contactussuccess.html')
            except Exception:
                pass
    return render(request, 'exam/contactus.html', {'form': form})


# ─── Admin Dashboard ─────────────────────────────────────────────────────────

@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    ctx = {
        'total_student': SMODEL.Student.objects.count(),
        'total_teacher': TMODEL.Teacher.objects.filter(status=True).count(),
        'total_course': models.Course.objects.count(),
        'total_question': models.Question.objects.count(),
        'total_academic_courses': models.AcademicCourse.objects.count(),
        'total_subjects': models.Subject.objects.count(),
        'recent_results': models.Result.objects.select_related('student__user', 'exam').order_by('-date')[:10],
    }
    return render(request, 'exam/admin_dashboard.html', ctx)


# ─── Teacher Management ──────────────────────────────────────────────────────

@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    ctx = {
        'total_teacher': TMODEL.Teacher.objects.filter(status=True).count(),
        'pending_teacher': TMODEL.Teacher.objects.filter(status=False).count(),
        'salary': TMODEL.Teacher.objects.filter(status=True).aggregate(Sum('salary'))['salary__sum'],
    }
    return render(request, 'exam/admin_teacher.html', ctx)


@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers = TMODEL.Teacher.objects.filter(status=True).select_related('user')
    return render(request, 'exam/admin_view_teacher.html', {'teachers': teachers})


@login_required(login_url='adminlogin')
def update_teacher_view(request, pk):
    teacher = get_object_or_404(TMODEL.Teacher, id=pk)
    user = User.objects.get(id=teacher.user_id)
    userForm = TFORM.TeacherUserForm(instance=user)
    teacherForm = TFORM.TeacherForm(instance=teacher)
    if request.method == 'POST':
        userForm = TFORM.TeacherUserForm(request.POST, instance=user)
        teacherForm = TFORM.TeacherForm(request.POST, request.FILES, instance=teacher)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            teacherForm.save()
            messages.success(request, 'Teacher updated successfully.')
            return redirect('admin-view-teacher')
    return render(request, 'exam/update_teacher.html', {'userForm': userForm, 'teacherForm': teacherForm})


@login_required(login_url='adminlogin')
def delete_teacher_view(request, pk):
    teacher = get_object_or_404(TMODEL.Teacher, id=pk)
    User.objects.filter(id=teacher.user_id).delete()
    teacher.delete()
    messages.success(request, 'Teacher deleted.')
    return redirect('admin-view-teacher')


@login_required(login_url='adminlogin')
def admin_view_pending_teacher_view(request):
    teachers = TMODEL.Teacher.objects.filter(status=False).select_related('user')
    return render(request, 'exam/admin_view_pending_teacher.html', {'teachers': teachers})


@login_required(login_url='adminlogin')
def approve_teacher_view(request, pk):
    salary_form = forms.TeacherSalaryForm()
    if request.method == 'POST':
        salary_form = forms.TeacherSalaryForm(request.POST)
        if salary_form.is_valid():
            teacher = get_object_or_404(TMODEL.Teacher, id=pk)
            teacher.salary = salary_form.cleaned_data['salary']
            teacher.status = True
            teacher.save()
            messages.success(request, 'Teacher approved.')
        return redirect('admin-view-pending-teacher')
    return render(request, 'exam/salary_form.html', {'teacherSalary': salary_form})


@login_required(login_url='adminlogin')
def reject_teacher_view(request, pk):
    teacher = get_object_or_404(TMODEL.Teacher, id=pk)
    User.objects.filter(id=teacher.user_id).delete()
    teacher.delete()
    messages.success(request, 'Teacher rejected.')
    return redirect('admin-view-pending-teacher')


@login_required(login_url='adminlogin')
def admin_view_teacher_salary_view(request):
    teachers = TMODEL.Teacher.objects.filter(status=True).select_related('user')
    return render(request, 'exam/admin_view_teacher_salary.html', {'teachers': teachers})


# ─── Student Management ───────────────────────────────────────────────────────

@login_required(login_url='adminlogin')
def admin_student_view(request):
    return render(request, 'exam/admin_student.html', {
        'total_student': SMODEL.Student.objects.count()
    })


@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students = SMODEL.Student.objects.select_related('user').all()
    return render(request, 'exam/admin_view_student.html', {'students': students})


@login_required(login_url='adminlogin')
def update_student_view(request, pk):
    student = get_object_or_404(SMODEL.Student, id=pk)
    user = User.objects.get(id=student.user_id)
    userForm = SFORM.StudentUserForm(instance=user)
    studentForm = SFORM.StudentForm(instance=student)
    if request.method == 'POST':
        userForm = SFORM.StudentUserForm(request.POST, instance=user)
        studentForm = SFORM.StudentForm(request.POST, request.FILES, instance=student)
        if userForm.is_valid() and studentForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            studentForm.save()
            messages.success(request, 'Student updated.')
            return redirect('admin-view-student')
    return render(request, 'exam/update_student.html', {'userForm': userForm, 'studentForm': studentForm})


@login_required(login_url='adminlogin')
def delete_student_view(request, pk):
    student = get_object_or_404(SMODEL.Student, id=pk)
    User.objects.filter(id=student.user_id).delete()
    student.delete()
    messages.success(request, 'Student deleted.')
    return redirect('admin-view-student')


@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students = SMODEL.Student.objects.select_related('user').all()
    return render(request, 'exam/admin_view_student_marks.html', {'students': students})


@login_required(login_url='adminlogin')
def admin_view_marks_view(request, pk):
    courses = models.Course.objects.all()
    response = render(request, 'exam/admin_view_marks.html', {'courses': courses})
    response.set_cookie('student_id', str(pk))
    return response


@login_required(login_url='adminlogin')
def admin_check_marks_view(request, pk):
    course = get_object_or_404(models.Course, id=pk)
    student_id = request.COOKIES.get('student_id')
    student = get_object_or_404(SMODEL.Student, id=student_id)
    results = models.Result.objects.filter(exam=course, student=student)
    return render(request, 'exam/admin_check_marks.html', {'results': results})


# ─── Course / Subject Management ─────────────────────────────────────────────

@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request, 'exam/admin_course.html')


@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm = forms.AcademicCourseForm()
    if request.method == 'POST':
        courseForm = forms.AcademicCourseForm(request.POST)
        if courseForm.is_valid():
            courseForm.save()
            messages.success(request, 'Academic course added.')
        return redirect('admin-view-course')
    return render(request, 'exam/admin_add_course.html', {'courseForm': courseForm})


@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.AcademicCourse.objects.prefetch_related('subjects').all()
    return render(request, 'exam/admin_view_course.html', {'courses': courses})


@login_required(login_url='adminlogin')
def delete_course_view(request, pk):
    get_object_or_404(models.AcademicCourse, id=pk).delete()
    messages.success(request, 'Course deleted.')
    return redirect('admin-view-course')


@login_required(login_url='adminlogin')
def admin_add_subject_view(request):
    subjectForm = forms.SubjectForm()
    if request.method == 'POST':
        subjectForm = forms.SubjectForm(request.POST)
        if subjectForm.is_valid():
            subjectForm.save()
            messages.success(request, 'Subject added.')
        return redirect('admin-view-subject')
    return render(request, 'exam/admin_add_subject.html', {'subjectForm': subjectForm})


@login_required(login_url='adminlogin')
def admin_view_subject_view(request):
    subjects = models.Subject.objects.select_related('academic_course').all()
    return render(request, 'exam/admin_view_subject.html', {'subjects': subjects})


@login_required(login_url='adminlogin')
def delete_subject_view(request, pk):
    get_object_or_404(models.Subject, id=pk).delete()
    messages.success(request, 'Subject deleted.')
    return redirect('admin-view-subject')


# ─── Question Management ──────────────────────────────────────────────────────

@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request, 'exam/admin_question.html')


@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm = forms.QuestionForm()
    courses = models.Course.objects.all()
    if request.method == 'POST':
        questionForm = forms.QuestionForm(request.POST)
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            course = get_object_or_404(models.Course, id=request.POST.get('courseID'))
            question.course = course
            question.save()
            messages.success(request, 'Question added.')
        return redirect('admin-view-question')
    return render(request, 'exam/admin_add_question.html', {
        'questionForm': questionForm, 'courses': courses
    })


@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses = models.Course.objects.annotate(q_count=Count('questions')).all()
    return render(request, 'exam/admin_view_question.html', {'courses': courses})


@login_required(login_url='adminlogin')
def view_question_view(request, pk):
    questions = models.Question.objects.filter(course_id=pk).select_related('course')
    course = get_object_or_404(models.Course, id=pk)
    return render(request, 'exam/view_question.html', {'questions': questions, 'course': course})


@login_required(login_url='adminlogin')
def delete_question_view(request, pk):
    get_object_or_404(models.Question, id=pk).delete()
    messages.success(request, 'Question deleted.')
    return redirect('admin-view-question')


# ─── Proctoring ───────────────────────────────────────────────────────────────

@login_required(login_url='adminlogin')
def admin_proctoring_view(request):
    alerts = models.ProctoringAlert.objects.select_related('student__user', 'course').all()[:200]
    return render(request, 'exam/admin_proctoring.html', {'alerts': alerts})
