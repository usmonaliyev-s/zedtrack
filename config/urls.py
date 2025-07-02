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
    path('teachers/<int:id>/edit/', edit_teacher),
    path('courses/<int:id>/edit/', edit_course),
    path('students/<int:id>/delete/confirmation/', delete_confirmation_student),
    path('students/<int:id>/delete/', delete_student),
    path('courses/<int:id>/delete/confirmation/', delete_confirmation_course),
    path('courses/<int:id>/delete/', delete_course),
    path('marking/', select_course),
    path('marking/course-id=<int:id>/', marking),
]
