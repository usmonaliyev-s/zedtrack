from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import ExpressionWrapper, FloatField, F, Count, Q
from django.db.models.functions import NullIf
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from attendance_tracker.models import Attendance
from courses.models import Course
from students.models import Student

import calendar
from collections import defaultdict
from datetime import date

import csv
from django.http import HttpResponse

def export_to_csv(filename, headers, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response

def no_permission(request):
    messages.error(request, 'You do not have a permission.')
    return redirect('dashboard')

def attendance_annotate(qs):
    return qs.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
    ).annotate(
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / NullIf(F('total'), 0),
            output_field=FloatField()
        )
    )

@login_required
def students_list(request):
    if hasattr(request.user, 'student_user'):
        return no_permission(request)

    role = "admin"
    students = attendance_annotate(Student.objects.all())

    if hasattr(request.user, 'teacher_user'):
        role = "teacher"
        students = students.filter(course__course_teacher__user=request.user)
    else:
        students = students.filter(center=request.user)

    if 'download-csv' in request.path:
        headers = ["First Name", "Last Name", "Course", "Phone Number", "Registration Date", "Gender"]
        rows = [[s.first_name, s.last_name, s.course, s.phone_number, s.registration_date, s.gender] for s in students]
        return export_to_csv('students', headers, rows)

    return render(request, "students/students_list.html", {"students": students, "role": role})

@login_required
def add_student(request):
    if hasattr(request.user, 'teacher_user') or hasattr(request.user, 'student_user'):
        return no_permission(request)
    data = {
        "courses": Course.objects.filter(center=request.user),
    }
    if request.method == "POST":
        user = User.objects.create_user(username=request.POST["username"], password=request.POST["password"])
        Student.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            gender=request.POST.get('gender'),
            course_id=request.POST.get('course'),
            registration_date=timezone.now().date(),
            center=request.user,
            user=user,
        )
        return redirect('student-list')

    return render(request, "students/add_student.html", data)

@login_required
def edit_student(request, id):
    if hasattr(request.user, 'teacher_user') or hasattr(request.user, 'student_user'):
        return no_permission(request)

    if request.method == "POST":
        student = get_object_or_404(Student, pk=id, center=request.user)
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')
        student.gender = request.POST.get('gender')
        student.course_id = request.POST.get('course')
        student.save()
        return redirect('student-list')
    student = get_object_or_404(Student, pk=id, center=request.user)
    courses = Course.objects.filter(center=request.user)

    data = {
        "student": student,
        "courses": courses,
    }
    return render(request, "students/edit_student.html", data)

@login_required
def delete_confirmation_student(request, id):
    if hasattr(request.user, 'teacher_user') or hasattr(request.user, 'student_user'):
        return no_permission(request)

    student = get_object_or_404(Student, pk=id, center=request.user)

    data = {
        "student": student,
    }
    return render(request, "students/delete_confirmation_student.html", data)

@login_required
def delete_student(request, id):
    if hasattr(request.user, 'teacher_user') or hasattr(request.user, 'student_user'):
        return no_permission(request)

    student = get_object_or_404(Student, pk=id, center=request.user).delete()
    return redirect('student-list')

@login_required
def student_details(request, id):
    if hasattr(request.user, 'teacher_user'):
        student = attendance_annotate(Student.objects.filter(course__course_teacher__user=request.user)).get(id=id)
        attendances = Attendance.objects.filter(student=student, course__course_teacher__user=request.user)
        raw_counts = Attendance.objects.filter(student_id=id, course__course_teacher__user=request.user).values('status').annotate(count=Count('id'))
    else:
        student = attendance_annotate(Student.objects.filter(center=request.user)).get(id=id)
        attendances = Attendance.objects.filter(student=student, center=request.user)
        raw_counts = Attendance.objects.filter(student_id=id, center=request.user).values('status').annotate(count=Count('id'))

    today = date.today()
    year, month = today.year, today.month
    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))

    attendance_map = {a.time.date(): a.status for a in attendances}

    day_map = {
        'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3,
        'Fri': 4, 'Sat': 5, 'Sun': 6,
    }
    raw_days = student.course.days
    target_weekdays = [day_map[d] for d in raw_days]

    # Build calendar grid
    calendar_weeks = []
    for i in range(0, len(month_days), 7):
        week = []
        for day in month_days[i:i+7]:
            is_course_day = day.weekday() in target_weekdays and day.month == month
            status = attendance_map.get(day) if is_course_day else None
            week.append((day, is_course_day, status))
        calendar_weeks.append(week)

    counts = defaultdict(int)
    for item in raw_counts:
        counts[item['status']] = item['count']

    chart_data = {
        "labels": ["Present", "Absent"],
        "values": [counts[True], counts[False]],
    }
    role = "admin"
    if hasattr(request.user, 'teacher_user'):
        role = "teacher"
    elif hasattr(request.user, 'student_user'):
        role = "student"
    data = {
        "student": student,
        "attendances": attendances,
        "latest_status": attendances.order_by('-time')[:1],
        "calendar_weeks": calendar_weeks,
        "month_name": today.strftime("%B"),
        "year": year,
        "today": today,
        "chart_data": chart_data,
        "attendance_records": attendances,
        "role": role
    }
    return render(request, "students/student_details.html", data)

@login_required
def student_dashboard(request):
    return student_details(request, Student.objects.get(user=request.user).id)