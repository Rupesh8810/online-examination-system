import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('student', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='AcademicCourse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150)),
                ('code', models.CharField(max_length=20)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('academic_course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subjects', to='exam.academiccourse')),
            ],
            options={'ordering': ['name']},
        ),
        migrations.AddConstraint(
            model_name='subject',
            constraint=models.UniqueConstraint(
                fields=('academic_course', 'code'), name='unique_subject_code'),
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('course_name', models.CharField(max_length=150)),
                ('question_number', models.PositiveIntegerField(default=10)),
                ('total_marks', models.PositiveIntegerField(default=100)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('duration_minutes', models.PositiveIntegerField(default=30)),
                ('max_attempts', models.PositiveIntegerField(default=1)),
                ('randomize_questions', models.BooleanField(default=True)),
                ('randomize_options', models.BooleanField(default=False)),
                ('quiz_file', models.FileField(blank=True, null=True, upload_to='quiz_files/')),
                ('answer_key_file', models.FileField(blank=True, null=True, upload_to='answer_keys/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subject', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='exams', to='exam.subject')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('marks', models.PositiveIntegerField(default=1)),
                ('question', models.CharField(max_length=600)),
                ('option1', models.CharField(max_length=200)),
                ('option2', models.CharField(max_length=200)),
                ('option3', models.CharField(max_length=200)),
                ('option4', models.CharField(max_length=200)),
                ('answer', models.CharField(
                    choices=[('Option1','Option1'),('Option2','Option2'),
                             ('Option3','Option3'),('Option4','Option4')],
                    max_length=200)),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='questions', to='exam.course')),
            ],
            options={'ordering': ['id']},
        ),
        migrations.CreateModel(
            name='ExamSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('session_token', models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)),
                ('status', models.CharField(
                    choices=[('active','Active'),('submitted','Submitted'),('expired','Expired')],
                    default='active', max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('question_order', models.JSONField(default=list)),
                ('answers', models.JSONField(default=dict)),
                ('tab_switch_count', models.PositiveIntegerField(default=0)),
                ('face_missing_count', models.PositiveIntegerField(default=0)),
                ('auto_submitted', models.BooleanField(default=False)),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sessions', to='exam.course')),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='exam_sessions', to='student.student')),
            ],
            options={'ordering': ['-started_at']},
        ),
        migrations.AddIndex(
            model_name='examsession',
            index=models.Index(
                fields=['student', 'course', 'status'],
                name='exam_session_lookup_idx'),
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('marks', models.PositiveIntegerField(default=0)),
                ('total_marks', models.PositiveIntegerField(default=0)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('tab_switch_count', models.PositiveIntegerField(default=0)),
                ('face_missing_count', models.PositiveIntegerField(default=0)),
                ('auto_submitted', models.BooleanField(default=False)),
                ('exam', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='results', to='exam.course')),
                ('session', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='exam.examsession')),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='results', to='student.student')),
            ],
            options={'ordering': ['-date']},
        ),
        migrations.AddIndex(
            model_name='result',
            index=models.Index(
                fields=['student', 'exam'],
                name='result_student_exam_idx'),
        ),
        migrations.CreateModel(
            name='ProctoringAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(
                    choices=[('no_face','No Face Detected'),
                             ('multiple_face','Multiple Faces Detected'),
                             ('face_away','Student Looking Away'),
                             ('tab_switch','Tab/Window Switch')],
                    max_length=50)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='proctoring_alerts', to='exam.course')),
                ('session', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='exam.examsession')),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='proctoring_alerts', to='student.student')),
            ],
            options={'ordering': ['-timestamp']},
        ),
        migrations.AddIndex(
            model_name='proctoringalert',
            index=models.Index(
                fields=['student', 'course'],
                name='proctor_student_course_idx'),
        ),
    ]
