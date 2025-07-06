from django.db.models import ExpressionWrapper, FloatField, F, Count, Q
from django.db.models.functions import NullIf
from django.shortcuts import render, redirect
from django.utils import timezone


from courses.models import Course
from students.models import Student



# Create your views here.
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
