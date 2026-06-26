from django import forms
from . import models


class CourseForm(forms.ModelForm):
    class Meta:
        model  = models.Course
        fields = [
            'course_name','subject','question_number','total_marks',
            'duration_minutes','start_time','end_time','max_attempts',
            'randomize_questions','randomize_options','is_active',
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type':'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time':   forms.DateTimeInput(attrs={'type':'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        for f in self.fields.values():
            if not isinstance(f.widget, forms.CheckboxInput):
                f.widget.attrs.setdefault('class','form-input')


class QuestionForm(forms.ModelForm):
    class Meta:
        model  = models.Question
        fields = ['marks','question','option1','option2','option3','option4','answer']
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class','form-input')


class AcademicCourseForm(forms.ModelForm):
    class Meta:
        model  = models.AcademicCourse
        fields = ['name','code','description']
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class','form-input')


class SubjectForm(forms.ModelForm):
    class Meta:
        model  = models.Subject
        fields = ['academic_course','name','code','description']
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class','form-input')


class QuizUploadForm(forms.ModelForm):
    class Meta:
        model  = models.Course
        fields = ['quiz_file','answer_key_file']
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class','form-input')


class TeacherSalaryForm(forms.Form):
    salary = forms.IntegerField()
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        self.fields['salary'].widget.attrs['class']='form-input'


class ContactusForm(forms.Form):
    Name    = forms.CharField(max_length=30)
    Email   = forms.EmailField()
    Message = forms.CharField(max_length=500, widget=forms.Textarea(attrs={'rows':3}))
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        for f in self.fields.values():
            f.widget.attrs.setdefault('class','form-input')
