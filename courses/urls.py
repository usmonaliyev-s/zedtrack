from django.urls import path

from .views import *

urlpatterns = [
    path('list/', courses_list, name='course-list'),
    path('add/', add_course, name='add-course'),
    path('edit/<int:id>/', edit_course, name='edit-course'),
    path('delete/<int:id>/confirmation/', delete_confirmation_course, name='delete-confirmation-course'),
    path('delete/<int:id>/', delete_course, name='delete-course'),
    path('details/<int:id>/', course_details, name='course-details'),
]