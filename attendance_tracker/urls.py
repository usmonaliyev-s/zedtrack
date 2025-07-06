from django.urls import path

from .views import *

urlpatterns = [
    path('', select_course, name='select-course'),
    path('selected-course=<int:pk>/', marking, name='selected-course'),
]