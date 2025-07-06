from django.urls import path

from .views import *

urlpatterns = [
    path('list/', courses_list, name='course-list'),
    path('add/', add_course, name='add-course'),
]