from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class CustomUser(AbstractUser):
    ROLES = (
    ('Admin', 'Admin'),
    ('Student', 'Student'),
    ('Teacher', 'Teacher'),
    )
    role = models.CharField(choices=ROLES, max_length=100)