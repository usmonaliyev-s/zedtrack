import json

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, ExpressionWrapper, F, FloatField
from django.db.models.functions import TruncDate, NullIf
from django.contrib import messages
from django.shortcuts import render, redirect
from datetime import date, timedelta, datetime

from attendance_tracker.models import Attendance
from courses.models import Course
from students.models import Student
from teachers.models import Teacher

from attendance_tracker.utilities import insights

def index(request):
    return render(request, 'index.html')

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

def dashboard(request, a=None, b=None, c=None):
    if request.user.is_authenticated:
        if hasattr(request.user, 'teacher_user'):
            return redirect('teacher-dashboard')
        elif hasattr(request.user, 'student_user'):
            return redirect('student-dashboard')
        predicted_attendance_rate = insights(request)
        students = Student.objects.annotate(
            total=Count('attendance'),
            total_lessons=Count('attendance'),
            absent=Count('attendance', filter=Q(attendance__status=False)),
            present=Count('attendance', filter=Q(attendance__status=True))
        ).filter(
            total__gt=0, center=request.user
            # absent__lt=2
        ).order_by('absent', '-present')[:5]

        students_low_attendance = attendance_annotate(Student.objects.all()).order_by('attendance_rate')[:10]
        top_student = attendance_annotate(Student.objects.all()).order_by('-attendance_rate')[:10]


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
        role = "admin"
        if hasattr(request.user, 'teacher_user'):
            role = "teacher"
        predicted_attendance_rate = insights(request)
        predicted_attendance_rate = json.loads(predicted_attendance_rate.content)
        data = {
            "students": Student.objects.filter(center=request.user),
            "top_students": top_student,
            "students_low_attendance": students_low_attendance,
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
            "role": role,
            "predicted_attendance_rate":predicted_attendance_rate,
        }
        return render(request, 'dashboard.html', data)
    else:
        return index(request)

@login_required
def select_course(request):
    if hasattr(request.user, 'student_user'):
        messages.error(request, 'You do not have a permission.')
        return redirect('dashboard')
    today = date.today()
    weekday = today.strftime("%a")
    courses = Course.objects.filter(days__contains=weekday, center=request.user)
    if hasattr(request.user, 'teacher_user'):
        courses = Course.objects.filter(days__contains=weekday, course_teacher__user=request.user)
    marked_courses = []
    for course in courses:
        has_attendance = Attendance.objects.filter(course=course, time__date=today, center=request.user).exists()
        if hasattr(request.user, 'teacher_user'):
            has_attendance = Attendance.objects.filter(course=course, time__date=today, course__course_teacher__user=request.user).exists()
        marked_courses.append({
            "course": course,
            "status": has_attendance,
            })
    role = "admin"
    if hasattr(request.user, 'teacher_user'):
        role = "teacher"
    data = {
        "courses": marked_courses,
        "role": role,
    }
    return render(request, "marking-attendance/select_course.html", data)

@login_required
def marking(request, id):
    if hasattr(request.user, 'student_user'):
        messages.error(request, 'You do not have a permission.')
        return redirect('dashboard')
    role = "admin"
    if hasattr(request.user, 'teacher_user'):
        students = Student.objects.annotate(
            total=Count('attendance'),
            present=Count('attendance', filter=Q(attendance__status=True)),
        ).annotate(
            attendance_rate=ExpressionWrapper(
                100.0 * F('present') / NullIf(F('total'), 0),
                output_field=FloatField()
            )
        ).filter(course__id=id, course__course_teacher__user=request.user)
        attendances = Attendance.objects.filter(course_id=id, time__date=date.today(),
                                                course__course_teacher__user=request.user)
        course = Course.objects.get(pk=id, course_teacher__user=request.user)
        role = "teacher"
    else:
        students = Student.objects.annotate(
            total=Count('attendance'),
            present=Count('attendance', filter=Q(attendance__status=True)),
        ).annotate(
            attendance_rate=ExpressionWrapper(
                100.0 * F('present') / NullIf(F('total'), 0),
                output_field=FloatField()
            )
        ).filter(course__id=id, center=request.user)
        attendances = Attendance.objects.filter(course_id=id, time__date=date.today(), center=request.user)
        course = Course.objects.get(pk=id, center=request.user)

    if request.method == "POST":
        for i in students:
            status = request.POST.get(f'status-{i.id}')
            if status == "present":
                status = True
            elif status == "absent":
                status = False
            if hasattr(request.user, 'teacher_user'):
                center = Teacher.objects.get(user=request.user).center
                Attendance.objects.create(student_id=i.id, course_id=id, status=status, center=center, user=request.user, marked_by=request.user)
            else:
                user = Course.objects.get(pk=id, center=request.user).course_teacher.user
                Attendance.objects.create(student_id=i.id, course_id=id, status=status, center=request.user, user=user, marked_by=request.user)
        return redirect("select-course")

    if attendances.exists():
        attendances = attendances
        marked_by = attendances[0].marked_by
    else:
        attendances = None
        marked_by = None

    data = {
        "students": students,
        "course": course,
        "attendances": attendances,
        "date": date.today(),
        "role": role,
        "marked_by": marked_by
    }
    return render(request, "marking-attendance/marking.html", data)

def history(request):
    if hasattr(request.user, 'student_user'):
        messages.error(request, 'You do not have a permission.')
        return redirect('dashboard')

    attendances = Attendance.objects.filter(center=request.user).order_by('-time')

    data = {
        'students': Student.objects.filter(center=request.user),
        'teachers': Teacher.objects.filter(center=request.user),
        'courses': Course.objects.filter(center=request.user),
        'attendances': attendances,
    }

    if request.method == "POST":
        a = request.GET.get('a')
        b = request.GET.get('b')
        student = request.GET.get('student')
        course = request.GET.get('course')
        teacher = request.GET.get('teacher')

        # start building query
        filters = Q(center=request.user)

        if a and b:
            data['a'] = a
            data['b'] = b
            a = datetime.strptime(a, "%Y-%m-%d").date()
            b = datetime.strptime(b, "%Y-%m-%d").date()
            filters &= Q(time__range=(a, b))

        if student and student != 'all':
            filters &= Q(student_id=student)
            data['student'] = Student.objects.get(pk=student)

        if course and course != 'all':
            filters &= Q(course_id=course)
            data['course'] = Course.objects.get(pk=course)

        if teacher and teacher != 'all':
            filters &= Q(course__course_teacher_id=teacher)
            data['teacher'] = Teacher.objects.get(pk=teacher)

        data['attendances'] = Attendance.objects.filter(filters).order_by('-time')

    return render(request, "marking-attendance/history.html", data)