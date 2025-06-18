from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import render
from datetime import date

from .models import Student, Teacher, Course, Attendance

def index(request):
    students = Student.objects.annotate(
        total=Count('attendance'),
        total_lessons=Count('attendance'),
        absent=Count('attendance', filter=Q(attendance__status=False)),
        present=Count('attendance', filter=Q(attendance__status=True))
    ).filter(
        total__gt=0,
        # absent__lt=2
    ).order_by('absent', '-present')

    gender_counts = Student.objects.values('gender').annotate(count=Count('id'))

    gender_data = {
        "labels": [("Male" if g["gender"] == "M" else "Female") for g in gender_counts],
        "values": [g["count"] for g in gender_counts]
    }

    absent_students = Student.objects.annotate(
        absents_today=Count('attendance', filter=Q(
            attendance__status=False,
            attendance__time__date=date.today()
        ))
    ).filter(
        absents_today__gt=0
    )
    attendance_trends = (
        Attendance.objects
        .filter(status=True)  # only students who were present
        .annotate(date=TruncDate('time'))  # extract date part
        .values('date')
        .annotate(count=Count('id'))  # count present students per day
        .order_by('date')
    )

    dates = [record["date"].strftime("%Y-%m-%d") for record in attendance_trends]
    counts = [record["count"] for record in attendance_trends]

    line_chart_data = {
        "labels": dates,
        "values": counts
    }

    data = {
        "students": Student.objects.all(),
        "top_students": students,
        "teachers": Teacher.objects.all(),
        "courses": Course.objects.all(),
        "absent_students": absent_students,
        "lessons": Attendance.objects.all(),
        "gender_data": gender_data,
        "line_chart_data":line_chart_data,
    }
    return render(request, 'index.html', data)
