from django.db.models import Count, Q, ExpressionWrapper, F, FloatField
from django.db.models.functions import TruncDate, NullIf
from django.shortcuts import render, redirect
from datetime import date

from attendance_tracker.models import Attendance
from courses.models import Course
from students.models import Student
from teachers.models import Teacher


# Create your views here.
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

    attendance_rate = (
        Attendance.objects.filter(status=True).count() /
        Attendance.objects.count()
        ) * 100 if Attendance.objects.exists() else 0

    present_today = Attendance.objects.filter(status=True, time__date=date.today()).count()
    total_today = Attendance.objects.filter(time__date=date.today()).count()

    attendance_rate_today = (
        (present_today / total_today) * 100
        if total_today > 0 else 0
    )
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
        "attendance_rate_today": attendance_rate_today,
        "todays_courses": todays_courses,
        "present_student": present_student,
        "date": date.today(),
        "attendance_records": Attendance.objects.all().order_by('-time')[:10],
    }
    return render(request, 'index.html', data)

def select_course(request):
    today = date.today()
    weekday = today.strftime("%a")
    courses = Course.objects.filter(days__contains=weekday)
    marked_courses = []
    for course in courses:
        has_attendance = Attendance.objects.filter(course=course, time__date=today).exists()
        marked_courses.append({
            "course": course,
            "status": has_attendance,
            })

    data = {
        "courses": marked_courses,
    }
    return render(request, "marking-attendance/select_course.html", data)

def marking(request, id):
    students = Student.objects.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
    ).annotate(
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / NullIf(F('total'), 0),
            output_field=FloatField()
        )
    ).filter(course__id=id)
    if request.method == "POST":
        for i in students:
            status = request.POST.get(f'status-{i.id}')
            if status == "present":
                status = True
            elif status == "absent":
                status = False
            Attendance.objects.create(student_id=i.id, course_id=id, status=status)
        return redirect("/marking/")
    attendances = Attendance.objects.filter(course_id=id, time__date=date.today())
    if attendances.exists():
        attendances = attendances
    else:
        attendances = None
    data = {
        "students": students,
        "course": Course.objects.get(pk=id),
        "attendances": attendances,
        "date": date.today()
    }
    return render(request, "marking-attendance/marking.html", data)