import uuid
from django.db import models
from django.utils import timezone
from student.models import Student


class AcademicCourse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} – {self.name}"


class Subject(models.Model):
    academic_course = models.ForeignKey(AcademicCourse, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['academic_course', 'code'], name='unique_subject_code')
        ]

    def __str__(self):
        return f"{self.code} – {self.name}"


class Course(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='exams')
    course_name = models.CharField(max_length=150)
    question_number = models.PositiveIntegerField(default=10)
    total_marks = models.PositiveIntegerField(default=100)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    max_attempts = models.PositiveIntegerField(default=1)
    randomize_questions = models.BooleanField(default=True)
    randomize_options = models.BooleanField(default=False)
    quiz_file = models.FileField(upload_to='quiz_files/', null=True, blank=True)
    answer_key_file = models.FileField(upload_to='answer_keys/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.course_name

    @property
    def is_currently_open(self):
        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    @property
    def time_slot_display(self):
        if self.start_time and self.end_time:
            fmt = "%d %b %Y %I:%M %p"
            return f"{self.start_time.strftime(fmt)} – {self.end_time.strftime(fmt)}"
        return "Open"


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    marks = models.PositiveIntegerField(default=1)
    question = models.CharField(max_length=600)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    ANSWER_CHOICES = (
        ('Option1', 'Option1'), ('Option2', 'Option2'),
        ('Option3', 'Option3'), ('Option4', 'Option4'),
    )
    answer = models.CharField(max_length=200, choices=ANSWER_CHOICES)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.question[:80]


class ExamSession(models.Model):
    STATUS_ACTIVE    = 'active'
    STATUS_SUBMITTED = 'submitted'
    STATUS_EXPIRED   = 'expired'
    STATUS_CHOICES = [
        (STATUS_ACTIVE,    'Active'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_EXPIRED,   'Expired'),
    ]
    session_token    = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    student          = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_sessions')
    course           = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    started_at       = models.DateTimeField(auto_now_add=True)
    expires_at       = models.DateTimeField()
    submitted_at     = models.DateTimeField(null=True, blank=True)
    question_order   = models.JSONField(default=list)
    answers          = models.JSONField(default=dict)
    tab_switch_count  = models.PositiveIntegerField(default=0)
    face_missing_count = models.PositiveIntegerField(default=0)
    auto_submitted   = models.BooleanField(default=False)

    class Meta:
        ordering = ['-started_at']
        indexes = [models.Index(fields=['student', 'course', 'status'])]

    def __str__(self):
        return f"{self.student} | {self.course} | {self.status}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def increment_tab(self):
        ExamSession.objects.filter(pk=self.pk).update(
            tab_switch_count=models.F('tab_switch_count') + 1)
        self.refresh_from_db(fields=['tab_switch_count'])
        return self.tab_switch_count

    def increment_face(self):
        ExamSession.objects.filter(pk=self.pk).update(
            face_missing_count=models.F('face_missing_count') + 1)
        self.refresh_from_db(fields=['face_missing_count'])
        return self.face_missing_count


class Result(models.Model):
    student   = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    exam      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results')
    session   = models.OneToOneField(ExamSession, on_delete=models.SET_NULL, null=True, blank=True)
    marks     = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    date      = models.DateTimeField(auto_now_add=True)
    tab_switch_count  = models.PositiveIntegerField(default=0)
    face_missing_count = models.PositiveIntegerField(default=0)
    auto_submitted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']
        indexes = [models.Index(fields=['student', 'exam'])]

    def __str__(self):
        return f"{self.student} – {self.exam} – {self.marks}/{self.total_marks}"

    @property
    def percentage(self):
        return round((self.marks / self.total_marks) * 100, 1) if self.total_marks else 0

    @property
    def grade(self):
        p = self.percentage
        if p >= 90: return 'A+'
        if p >= 75: return 'A'
        if p >= 60: return 'B'
        if p >= 45: return 'C'
        if p >= 33: return 'D'
        return 'F'


class ProctoringAlert(models.Model):
    ALERT_TYPES = [
        ('no_face',       'No Face Detected'),
        ('multiple_face', 'Multiple Faces Detected'),
        ('face_away',     'Student Looking Away'),
        ('tab_switch',    'Tab/Window Switch'),
    ]
    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='proctoring_alerts')
    course     = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='proctoring_alerts')
    session    = models.ForeignKey(ExamSession, on_delete=models.SET_NULL, null=True, blank=True)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['student', 'course'])]

    def __str__(self):
        return f"{self.student} – {self.alert_type} @ {self.timestamp:%Y-%m-%d %H:%M}"
