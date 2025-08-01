from django.db import models
from multiselectfield import MultiSelectField
from django.contrib.auth.models import User

from teachers.models import Teacher

# Create your models here.
class Course(models.Model):
    DAYS_OF_WEEK = (
        ('Mon', 'Monday'),
        ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'),
        ('Fri', 'Friday'),
        ('Sat', 'Saturday'),
        ('Sun', 'Sunday'),
    )
    course_name = models.CharField(max_length=100)
    course_teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course_time = models.TimeField()
    days = MultiSelectField(choices=DAYS_OF_WEEK)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.course_name