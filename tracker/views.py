from itertools import count

from django.db.models import Count, Q
from django.shortcuts import render

from .models import *

from datetime import datetime

top_students = Student.objects.annotate(
    total=Count('attendance'),
    absent=Count('attendance', filter=Q(attendance__status=False))
).filter(
    total__gt=5,
    absent=0
)

absent_students = Student.objects.annotate(total=Count('attendance', filter=Q(attendance__status=False))).filter(attendance__time=datetime.today())

def index(request):
    data = {
        "students": Student.objects.all(),
        "teachers": Teacher.objects.all(),
        "top_students": top_students,
        "courses": Course.objects.all(),
        "absent_students": absent_students,
    }
    return render(request, 'index.html', data)