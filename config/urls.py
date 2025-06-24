from django.contrib import admin
from django.urls import path

from tracker.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),
    path('students/', students_list),
    path('teachers/', teachers_list),
    path('courses/', courses_list),
    path('students/add/', add_student),
    path('teachers/add/', add_teacher),
    path('courses/add/', add_course),
    path('students/<int:id>/edit/', edit_student),
]
