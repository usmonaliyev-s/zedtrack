from django.db.models import Count, Q, ExpressionWrapper, F
from django.db.models.fields import FloatField
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
    ).order_by('absent', '-present')[:5]

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

    present_student = Student.objects.annotate(
        absents_today=Count('attendance', filter=Q(
            attendance__status=True,
            attendance__time__date=date.today()
        ))
    ).filter(
        absents_today__gt=0
    )

    attendance_trends = (
        Attendance.objects
        .filter(status=True)
        .annotate(date=TruncDate('time'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    dates = [record["date"].strftime("%Y-%m-%d") for record in attendance_trends]
    counts = [record["count"] for record in attendance_trends]

    todays_courses = 0
    today = date.today().strftime("%a")
    for i in Course.objects.all():
        if today in i.days:
            todays_courses += 1
    line_chart_data = {
        "labels": dates,
        "values": counts
    }

    attendance_rate = (Attendance.objects.filter(status=True).count() / Attendance.objects.count()) * 100

    data = {
        "students": Student.objects.all(),
        "top_students": students,
        "teachers": Teacher.objects.all(),
        "courses": Course.objects.all(),
        "absent_students": absent_students,
        "lessons": Attendance.objects.all(),
        "gender_data": gender_data,
        "line_chart_data":line_chart_data,
        "attendance_rate": attendance_rate,
        "todays_courses": todays_courses,
        "present_student": present_student,
    }
    return render(request, 'index.html', data)

def students_list(request):

    students = Student.objects.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
    ).annotate(
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / F('total'),
            output_field=FloatField()
        )
    ).filter(
        total__gt=0  # Avoid division by zero
    )
    data = {
        "students": students,
    }
    return render(request, "students_list.html", data)

def teachers_list(request):
    teachers = Teacher.objects.annotate(
    num_students=Count('course__student', distinct=True)
)
    data = {
        "teachers": teachers,
    }
    return render(request, "teachers_list.html", data)

def courses_list(request):
    courses = Course.objects.all()
    data = {
        "courses": courses,
    }
    return render(request, "courses_list.html", data)