from django.db.models import Count, Q, ExpressionWrapper, F
from django.db.models.fields import FloatField
from django.db.models.functions import TruncDate, NullIf
from django.shortcuts import render, redirect
from datetime import date
from django.utils import timezone

from .models import *

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

"""
Views related to Students
"""
def students_list(request):
    students = Student.objects.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
    ).annotate(
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / NullIf(F('total'), 0),
            output_field=FloatField()
        )
    )

    data = {
        "students": students,
    }
    return render(request, "students/students_list.html", data)

def add_student(request):
    data = {
        "courses": Course.objects.all(),
    }
    if request.method == "POST":
        print(request.POST.get('gender'))
        Student.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            gender=request.POST.get('gender'),
            course_id=request.POST.get('course'),
            registration_date=timezone.now().date()
        )
        return redirect('/students/')

    return render(request, "students/add_student.html", data)


def edit_student(request, id):
    if request.method == "POST":
        student = Student.objects.get(pk=id)
        student.first_name = request.POST.get('first_name')
        student.last_name = request.POST.get('last_name')
        student.gender = request.POST.get('gender')
        student.course_id = request.POST.get('course')
        student.save()
        return redirect('/students/')
    student = Student.objects.get(id=id)
    courses = Course.objects.all()
    # print(student.gender)
    data = {
        "student": student,
        "courses": courses,
    }
    return render(request, "students/edit_student.html", data)

def delete_confirmation_student(request, id):
    student = Student.objects.get(pk=id)
    data = {
        "student": student,
    }
    return render(request, "students/delete_confirmation_student.html", data)

def delete_student(request, id):
    Student.objects.get(pk=id).delete()
    return redirect('/students/')

"""
Views related to teachers
"""
def teachers_list(request):
    teachers = Teacher.objects.annotate(
    num_students=Count('course__student', distinct=True),
    num_courses=Count("course", distinct=True)
    )
    data = {
        "teachers": teachers,
    }
    return render(request, "teachers/teachers_list.html", data)

def add_teacher(request):
    if request.method == "POST":
        Teacher.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone_number=request.POST.get('phone_number'),
        )
        return redirect('/teachers/')

    return render(request, "teachers/add_teacher.html")


def edit_teacher(request, id):
    if request.method == "POST":
        teacher = Teacher.objects.get(pk=id)
        teacher.first_name = request.POST.get('first_name')
        teacher.last_name = request.POST.get('last_name')
        teacher.phone_number = request.POST.get('phone_number')
        teacher.save()
        return redirect('/teachers/')
    teacher = Teacher.objects.get(id=id)
    data = {
        "teacher": teacher,
    }
    return render(request, "teachers/edit_teacher.html", data)

def delete_confirmation_teacher(request, id):
    teacher = Teacher.objects.get(pk=id)
    data = {
        "teacher": teacher,
    }
    return render(request, "teachers/delete_confirmation_teacher.html", data)

def delete_teacher(request, id):
    Teacher.objects.get(pk=id).delete()
    return redirect('/teachers/')


"""
Views related to course
"""
def courses_list(request):
    courses = Course.objects.annotate(num_students=Count('student', distinct=True))
    data = {
        "courses": courses,
    }
    return render(request, "courses/courses_list.html", data)


def add_course(request):
    data = {
        "teachers": Teacher.objects.all(),
    }
    if request.method == "POST":
        Course.objects.create(
            course_name=request.POST.get('course_name'),
            course_teacher_id=request.POST.get('teacher'),
            course_time=request.POST.get('course_time'),
            days=request.POST.getlist('days'),
            description=request.POST.get('description'),
        )
        return redirect('/courses/')

    return render(request, "courses/add_course.html", data)

def edit_course(request, id):
    if request.method == "POST":
        course = Course.objects.get(pk=id)
        course.course_name = request.POST.get('name')
        course.course_teacher_id = request.POST.get('teacher')
        course.course_time = request.POST.get('time')
        course.days = request.POST.getlist('days')
        course.description = request.POST.getlist('description')
        course.save()
        return redirect('/courses/')
    course = Course.objects.get(id=id)
    data = {
        "course": course,
        "teachers": Teacher.objects.all(),
        "days": course.days,
    }
    return render(request, "courses/edit_course.html", data)