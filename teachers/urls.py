from django.urls import path

from .views import *

urlpatterns = [
    path('list/', teachers_list, name='teachers-list'),
    path('add/', add_teacher, name='add-teacher'),
]