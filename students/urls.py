from django.urls import path

from .views import *

urlpatterns = [
    path('list/', students_list, name='student-list'),
    path('list/download-csv/', students_list, name='student-list-csv'),
    path('add/', add_student, name='add-student'),
    path('delete/<int:id>/confirmation/', delete_confirmation_student, name='delete-confirmation-student'),
    path('delete/<int:id>/', delete_student, name='delete-student'),
    path('edit/<int:id>/', edit_student, name='edit-student'),
    path('details/<int:id>/', student_details, name="student-details"),
    path('', student_dashboard, name='student-dashboard')
]