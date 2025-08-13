from django.urls import path

from .views import *

urlpatterns = [
    path('', select_course, name='select-course'),
    path('selected-course/<int:id>/', marking, name='selected-course'),
    path('history/', history, name='attendance-history'),
]