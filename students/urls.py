from django.urls import path

from .views import *

urlpatterns = [
    path('list/', students_list, name='student-list'),
    path('add/', add_student, name='add-student'),
]