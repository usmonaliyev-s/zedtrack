from django.urls import path

from .views import *

urlpatterns = [
    path('list/', teachers_list, name='teachers-list'),
    path('add/', add_teacher, name='add-teacher'),
    path('edit/<int:id>/', edit_teacher, name='edit-teacher'),
    path('delete/<int:id>/confirmation/', delete_confirmation_teacher, name='delete-confirmation-teacher'),
    path('delete/<int:id>/', delete_teacher, name='delete-teacher'),
]