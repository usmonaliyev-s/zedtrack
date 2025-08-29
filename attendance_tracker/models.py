from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from courses.models import Course
from students.models import Student

# Create your models here.
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name='Attendance status', default=False)
    center = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="user")
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="Created_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course', 'time'],
                name='unique_attendance_record'
            )
        ]

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.time} - {self.course} - {self.status}"