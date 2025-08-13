from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from django.db.models.functions import NullIf, TruncDate
from django.shortcuts import render, redirect, get_object_or_404

from attendance_tracker.models import Attendance
from attendance_tracker.views import index
from courses.models import Course
from students.models import Student
from teachers.models import Teacher

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
    messages.error(request, 'You do not have permission.')
    return redirect('dashboard')

def is_teacher_or_student(user):
    return hasattr(user, 'teacher_user') or hasattr(user, 'student_user')

def get_teacher(pk, user):
    return get_object_or_404(Teacher, pk=pk, center=user)

@login_required
def teachers_list(request):
    if is_teacher_or_student(request.user):
        return no_permission(request)
    teachers = Teacher.objects.annotate(
        num_students=Count('course__student', distinct=True),
        num_courses=Count('course', distinct=True)
    ).filter(center=request.user)

    if 'download-csv' in request.path:
        headers = ["First Name", "Last Name", "Phone Number"]
        rows = [[s.first_name, s.last_name, s.phone_number] for s in teachers]
        return export_to_csv('teachers-list', headers, rows)

    return render(request, "teachers/teachers_list.html", {"teachers": teachers})

@login_required
def add_teacher(request):
    if is_teacher_or_student(request.user):
        return no_permission(request)
    if request.method == "POST":
        user = User.objects.create_user(
            username=request.POST['username'], password=request.POST['password']
        )
        Teacher.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone_number=request.POST.get('phone_number'),
            center=request.user, user=user
        )
        return redirect('teachers-list')
    return render(request, "teachers/add_teacher.html")

@login_required
def edit_teacher(request, id):
    if is_teacher_or_student(request.user):
        return no_permission(request)
    teacher = get_teacher(id, request.user)
    if request.method == "POST":
        for field in ["first_name", "last_name", "phone_number"]:
            setattr(teacher, field, request.POST.get(field))
        teacher.save()
        return redirect('teachers-list')
    return render(request, "teachers/edit_teacher.html", {"teacher": teacher})

@login_required
def delete_confirmation_teacher(request, id):
    if is_teacher_or_student(request.user):
        return no_permission(request)
    return render(request, "teachers/delete_confirmation_teacher.html",
                  {"teacher": get_teacher(id, request.user)})

@login_required
def delete_teacher(request, id):
    if is_teacher_or_student(request.user):
        return no_permission(request)
    get_teacher(id, request.user).delete()
    return redirect('teachers-list')

@login_required
def teacher_details(request, id):
    if hasattr(request.user, 'student_user'):
        return no_permission(request)
    teacher = get_teacher(id, request.user)
    courses = Course.objects.filter(course_teacher=teacher, center=request.user)
    students = Student.objects.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / NullIf(F('total'), 0), output_field=FloatField()
        )
    ).filter(course__course_teacher=teacher, center=request.user)
    return render(request, "teachers/teacher_details.html", {
        "teacher": teacher, "courses": courses, "students": students
    })

@login_required
def teacher_dashboard(request, a=None):
    if hasattr(request.user, 'student_user'):
        return no_permission(request)
    if not hasattr(request.user, 'teacher_user'):
        return index(request)

    user = request.user
    students = Student.objects.annotate(
        total=Count('attendance'),
        absent=Count('attendance', filter=Q(attendance__status=False)),
        present=Count('attendance', filter=Q(attendance__status=True))
    ).filter(total__gt=0, course__course_teacher__user=user).order_by('absent', '-present')[:5]

    absent_students = Student.objects.annotate(
        absents_today=Count('attendance', filter=Q(
            attendance__status=False, attendance__time__date=date.today()
        ))
    ).filter(absents_today__gt=0, course__course_teacher__user=user)

    present_student = Student.objects.annotate(
        presents_today=Count('attendance', filter=Q(
            attendance__status=True, attendance__time__date=date.today()
        ))
    ).filter(presents_today__gt=0, course__course_teacher__user=user)

    attendance_trends = Attendance.objects.filter(
        course__course_teacher__user=user
    ).annotate(date=TruncDate('time')).values('date').annotate(count=Count('id')).order_by('date')

    if a:
        start = date.today() - timedelta(days=a)
        attendance_trends = attendance_trends.filter(date__range=(start, date.today()))

    line_chart_data = {
        "labels": [rec["date"].strftime("%Y-%m-%d") for rec in attendance_trends],
        "values": [rec["count"] for rec in attendance_trends]
    }

    today_name = date.today().strftime("%a")
    todays_courses = sum(1 for c in Course.objects.filter(course_teacher__user=user) if today_name in c.days)

    total_attendance = Attendance.objects.filter(course__course_teacher__user=user)
    attendance_rate = (
        total_attendance.filter(status=True).count() / total_attendance.count() * 100
        if total_attendance.exists() else 0
    )

    present_today = total_attendance.filter(status=True, time__date=date.today()).count()
    total_today = total_attendance.filter(time__date=date.today()).count()
    attendance_rate_today = (present_today / total_today) * 100 if total_today else 0

    data = {
        "students": Student.objects.filter(course__course_teacher__user=user),
        "top_students": students,
        "courses": Course.objects.filter(course_teacher__user=user),
        "absent_students": absent_students,
        "lessons": total_attendance,
        "line_chart_data": line_chart_data,
        "attendance_rate": attendance_rate,
        "attendance_rate_today": attendance_rate_today,
        "todays_courses": todays_courses,
        "present_student": present_student,
        "date": date.today(),
        "attendance_records": total_attendance.order_by('-time')[:10],
        "role": "teacher"
    }
    return render(request, 'teachers/dashboard.html', data)
