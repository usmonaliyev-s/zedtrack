from django.db.models import Count, Q, ExpressionWrapper, F
from django.db.models.fields import FloatField
from django.db.models.functions import NullIf
from django.shortcuts import render, redirect

from courses.models import Course
from students.models import Student
from teachers.models import Teacher


# Create your views here.
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
        return redirect('/course/list/')

    return render(request, "courses/add_course.html", data)

def edit_course(request, id):
    if request.method == "POST":
        course = Course.objects.get(pk=id)
        course.course_name = request.POST.get('name')
        course.course_teacher_id = request.POST.get('teacher')
        course.course_time = request.POST.get('time')
        course.days = request.POST.getlist('days')
        course.description = request.POST.get('description')
        course.save()
        return redirect('/course/list/')
    course = Course.objects.get(id=id)
    data = {
        "course": course,
        "teachers": Teacher.objects.all(),
        "days": course.days,
    }
    return render(request, "courses/edit_course.html", data)

def delete_confirmation_course(request, id):
    course = Course.objects.get(pk=id)
    data = {
        "course": course,
    }
    return render(request, "courses/delete_confirmation_course.html", data)

def delete_course(request, id):
    Course.objects.get(pk=id).delete()
    return redirect('/course/list/')

def course_details(request, id):
    course = Course.objects.get(pk=id)
    students = Student.objects.annotate(
        total=Count('attendance'),
        present=Count('attendance', filter=Q(attendance__status=True)),
    ).annotate(
        attendance_rate=ExpressionWrapper(
            100.0 * F('present') / NullIf(F('total'), 0),
            output_field=FloatField()
        )
    ).filter(course=course)
    data = {
        "course": course,
        "students": students,
    }
    return render(request, "courses/course_details.html", data)
