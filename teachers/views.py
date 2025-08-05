from datetime import date, timedelta
from attendance_tracker.models import Attendance

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models.functions import NullIf, TruncDate
from django.shortcuts import render, redirect
from django.db.models import ExpressionWrapper, FloatField, F, Count, Q

from attendance_tracker.views import index
from courses.models import Course
from students.models import Student
from teachers.models import Teacher


# Create your views here.
@login_required
def teachers_list(request):
    if hasattr(request.user, 'teacher_user'):
        return redirect('teacher-dashboard')
    teachers = Teacher.objects.annotate(
    num_students=Count('course__student', distinct=True),
    num_courses=Count("course", distinct=True)
    ).filter(center=request.user)
    data = {
        "teachers": teachers,
    }
    return render(request, "teachers/teachers_list.html", data)

@login_required
def add_teacher(request):
    if hasattr(request.user, 'teacher_user'):
        return redirect('teacher-dashboard')
    if request.method == "POST":
        user = User.objects.create_user(username=request.POST['username'], password=request.POST['password'])
        Teacher.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone_number=request.POST.get('phone_number'),
            center = request.user,
            user=user,
        )
        return redirect('teachers-list')

    return render(request, "teachers/add_teacher.html")

@login_required
def edit_teacher(request, id):
    if hasattr(request.user, 'teacher_user'):
        return redirect('teacher-dashboard')
    if request.method == "POST":
        teacher = Teacher.objects.get(pk=id, center=request.user)
        teacher.first_name = request.POST.get('first_name')
        teacher.last_name = request.POST.get('last_name')
        teacher.phone_number = request.POST.get('phone_number')
        teacher.save()
        return redirect('teachers-list')
    teacher = Teacher.objects.get(id=id, center=request.user)
    data = {
        "teacher": teacher,
    }
    return render(request, "teachers/edit_teacher.html", data)

@login_required
def delete_confirmation_teacher(request, id):
    if hasattr(request.user, 'teacher_user'):
        return redirect('teacher-dashboard')
    teacher = Teacher.objects.get(pk=id, center=request.user)
    data = {
        "teacher": teacher,
    }
    return render(request, "teachers/delete_confirmation_teacher.html", data)

@login_required
def delete_teacher(request, id):
    if hasattr(request.user, 'teacher_user'):
        return redirect('teacher-dashboard')
    Teacher.objects.get(pk=id, center=request.user).delete()
    return redirect('teachers-list')

@login_required
def teacher_details(request, id):
    if hasattr(request.user, 'teacher_user'):
        return redirect('teacher-dashboard')
    teacher = Teacher.objects.get(pk=id, center=request.user)
    courses = Course.objects.filter(course_teacher=teacher, center=request.user)
    students = Student.objects.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
    ).annotate(
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / NullIf(F('total'), 0),
            output_field=FloatField()
        )
    ).filter(course__course_teacher=teacher, center=request.user)
    data = {
        "teacher": teacher,
        "courses": courses,
        "students": students,
    }
    return render(request, "teachers/teacher_details.html", data)

@login_required
def teacher_dashboard(request, a=None):
    if request.user.is_authenticated and hasattr(request.user, 'teacher_user'):
        students = Student.objects.annotate(
            total=Count('attendance'),
            total_lessons=Count('attendance'),
            absent=Count('attendance', filter=Q(attendance__status=False)),
            present=Count('attendance', filter=Q(attendance__status=True))
        ).filter(
            total__gt=0, course__course_teacher__user=request.user
        ).order_by('absent', '-present')[:5]

        absent_students = Student.objects.annotate(
            absents_today=Count('attendance', filter=Q(
                attendance__status=False,
                attendance__time__date=date.today()
            ))
        ).filter(
            absents_today__gt=0, course__course_teacher__user=request.user
        )

        present_student = Student.objects.annotate(
            absents_today=Count('attendance', filter=Q(
                attendance__status=True,
                attendance__time__date=date.today()
            ))
        ).filter(
            absents_today__gt=0, course__course_teacher__user=request.user
        )

        attendance_trends = (
            Attendance.objects
            .filter(course__course_teacher__user=request.user)
            .annotate(date=TruncDate('time'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        if a:
            a = date.today() - timedelta(days=a)
            b = date.today()
            attendance_trends = attendance_trends.filter(date__range=(a, b))
        dates = [record["date"].strftime("%Y-%m-%d") for record in attendance_trends]
        counts = [record["count"] for record in attendance_trends]

        todays_courses = 0
        today = date.today().strftime("%a")
        for i in Course.objects.filter(course_teacher__user=request.user):
            if today in i.days:
                todays_courses += 1
        line_chart_data = {
            "labels": dates,
            "values": counts
        }

        attendance_rate = (
            Attendance.objects.filter(status=True, course__course_teacher__user=request.user).count() /
            Attendance.objects.filter(course__course_teacher__user=request.user).count()
            ) * 100 if Attendance.objects.filter(course__course_teacher__user=request.user).exists() else 0

        present_today = Attendance.objects.filter(status=True, time__date=date.today(), course__course_teacher__user=request.user).count()
        total_today = Attendance.objects.filter(time__date=date.today(), course__course_teacher__user=request.user).count()

        attendance_rate_today = (
            (present_today / total_today) * 100
            if total_today > 0 else 0
        )
        role = "admin"
        if hasattr(request.user, 'teacher_user'):
            role = "teacher"
        data = {
            "students": Student.objects.filter(course__course_teacher__user=request.user),
            "top_students": students,
            "courses": Course.objects.filter(course_teacher__user=request.user),
            "absent_students": absent_students,
            "lessons": Attendance.objects.filter(course__course_teacher__user=request.user),
            "line_chart_data":line_chart_data,
            "attendance_rate": attendance_rate,
            "attendance_rate_today": attendance_rate_today,
            "todays_courses": todays_courses,
            "present_student": present_student,
            "date": date.today(),
            "attendance_records": Attendance.objects.filter(course__course_teacher__user=request.user).order_by('-time')[:10],
            "role": role
        }
        return render(request, 'teachers/dashboard.html', data)
    else:
        return index(request)