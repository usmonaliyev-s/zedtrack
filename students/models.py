from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from courses.models import Course

# Create your models here.
class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    registration_date = models.DateField(auto_now_add=True)
    center = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_center')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_user')

    def __str__(self):
        return self.first_name + " " + self.last_name