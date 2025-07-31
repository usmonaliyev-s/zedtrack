from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, ExpressionWrapper, F, FloatField
from django.db.models.functions import TruncDate, NullIf
from django.shortcuts import render, redirect
from datetime import date, timedelta

from attendance_tracker.models import Attendance
from courses.models import Course
from students.models import Student
from teachers.models import Teacher


def index(request):
    return render(request, 'index.html')

@login_required
def dashboard(request, a=None, b=None, c=None):
    if request.user.is_authenticated:
        students = Student.objects.annotate(
            total=Count('attendance'),
            total_lessons=Count('attendance'),
            absent=Count('attendance', filter=Q(attendance__status=False)),
            present=Count('attendance', filter=Q(attendance__status=True))
        ).filter(
            total__gt=0, center=request.user
            # absent__lt=2
        ).order_by('absent', '-present')[:5]

        gender_counts = Student.objects.filter(center=request.user).values('gender').annotate(count=Count('id'))

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
            absents_today__gt=0, center=request.user
        )

        present_student = Student.objects.annotate(
            absents_today=Count('attendance', filter=Q(
                attendance__status=True,
                attendance__time__date=date.today()
            ))
        ).filter(
            absents_today__gt=0, center=request.user
        )

        attendance_trends = (
            Attendance.objects
            .filter(center=request.user)
            .annotate(date=TruncDate('time'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        if a and b:
            attendance_trends = attendance_trends.filter(date__range=(a, b))
        elif c:
            a = date.today() - timedelta(days=c)
            b = date.today()
            attendance_trends = attendance_trends.filter(date__range=(a, b))
        dates = [record["date"].strftime("%Y-%m-%d") for record in attendance_trends]
        counts = [record["count"] for record in attendance_trends]

        todays_courses = 0
        today = date.today().strftime("%a")
        for i in Course.objects.filter(center=request.user):
            if today in i.days:
                todays_courses += 1
        line_chart_data = {
            "labels": dates,
            "values": counts
        }

        attendance_rate = (
            Attendance.objects.filter(status=True, center=request.user).count() /
            Attendance.objects.filter(center=request.user).count()
            ) * 100 if Attendance.objects.filter(center=request.user).exists() else 0

        present_today = Attendance.objects.filter(status=True, time__date=date.today(), center=request.user).count()
        total_today = Attendance.objects.filter(time__date=date.today(), center=request.user).count()

        attendance_rate_today = (
            (present_today / total_today) * 100
            if total_today > 0 else 0
        )
        data = {
            "students": Student.objects.filter(center=request.user),
            "top_students": students,
            "teachers": Teacher.objects.filter(center=request.user),
            "courses": Course.objects.filter(center=request.user),
            "absent_students": absent_students,
            "lessons": Attendance.objects.filter(center=request.user),
            "gender_data": gender_data,
            "line_chart_data":line_chart_data,
            "attendance_rate": attendance_rate,
            "attendance_rate_today": attendance_rate_today,
            "todays_courses": todays_courses,
            "present_student": present_student,
            "date": date.today(),
            "attendance_records": Attendance.objects.filter(center=request.user).order_by('-time')[:10],
        }
        return render(request, 'dashboard.html', data)
    else:
        return index(request)

@login_required
def select_course(request):
    today = date.today()
    weekday = today.strftime("%a")
    courses = Course.objects.filter(days__contains=weekday, center=request.user)
    marked_courses = []
    for course in courses:
        has_attendance = Attendance.objects.filter(course=course, time__date=today, center=request.user).exists()
        marked_courses.append({
            "course": course,
            "status": has_attendance,
            })

    data = {
        "courses": marked_courses,
    }
    return render(request, "marking-attendance/select_course.html", data)

@login_required
def marking(request, id):
    students = Student.objects.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
    ).annotate(
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / NullIf(F('total'), 0),
            output_field=FloatField()
        )
    ).filter(course__id=id, center=request.user)
    if request.method == "POST":
        for i in students:
            status = request.POST.get(f'status-{i.id}')
            if status == "present":
                status = True
            elif status == "absent":
                status = False
            Attendance.objects.create(student_id=i.id, course_id=id, status=status, center=request.user)
        return redirect("select-course")
    attendances = Attendance.objects.filter(course_id=id, time__date=date.today(), center=request.user)
    if attendances.exists():
        attendances = attendances
    else:
        attendances = None
    data = {
        "students": students,
        "course": Course.objects.get(pk=id, center=request.user),
        "attendances": attendances,
        "date": date.today()
    }
    return render(request, "marking-attendance/marking.html", data)