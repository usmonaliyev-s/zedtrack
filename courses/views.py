from django.db.models import Count, Q, ExpressionWrapper, F
from django.db.models.fields import FloatField
from django.db.models.functions import NullIf
from django.shortcuts import render, redirect

from courses.models import Course
from students.models import Student
from teachers.models import Teacher

from datetime import date
import calendar


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

    # Handle days
    day_map = {
        'Mon': 0, 'Monday': 0,
        'Tue': 1, 'Tues': 1, 'Tuesday': 1,
        'Wed': 2, 'Wednesday': 2,
        'Thu': 3, 'Thurs': 3, 'Thursday': 3,
        'Fri': 4, 'Friday': 4,
        'Sat': 5, 'Saturday': 5,
        'Sun': 6, 'Sunday': 6,
    }
    raw_days = course.days
    target_weekdays = [day_map[d] for d in raw_days]

    # Get calendar for current month
    today = date.today()
    year, month = today.year, today.month
    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))  # Includes days from prev/next month to fill full weeks

    # Build a list of weeks, each week is a list of (date, is_course_day)
    weeks = []
    for i in range(0, len(month_days), 7):
        week = []
        for day in month_days[i:i+7]:
            is_course_day = (day.weekday() in target_weekdays and day.month == month)
            week.append((day, is_course_day))
        weeks.append(week)

    data = {
        "course": course,
        "students": students,
        "calendar_weeks": weeks,
        "month_name": today.strftime("%B"),
        "year": year,
        "today": today,
    }
    return render(request, "courses/course_details.html", data)
