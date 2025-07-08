from django.db import models

from courses.models import Course
from students.models import Student

# Create your models here.
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name='Attence status', default=False)

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.time} - {self.course} - {self.status}"