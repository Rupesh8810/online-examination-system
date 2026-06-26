from django.db import models
from django.contrib.auth.models import User


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/Teacher/', null=True, blank=True)
    address = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=20)
    status = models.BooleanField(default=False)
    salary = models.PositiveIntegerField(null=True, blank=True)

    @property
    def get_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def get_instance(self):
        return self

    def __str__(self):
        return self.get_name
