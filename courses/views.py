from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Course, Lesson, CourseEnrollment, CourseLike, CourseReview, Category

def course_list(request):
    courses = Course.objects.filter(is_published=True).select_related('instructor', 'category').prefetch_related('likes', 'reviews')
    categories = Category.objects.all()
    
    # Фильтрация
    category_id = request.GET.get('category')
    level = request.GET.get('level')
    
    if category_id:
        courses = courses.filter(category_id=category_id)
    if level:
        courses = courses.filter(level=level)
    
    context = {
        'courses': courses,
        'categories': categories,
    }
    return render(request, 'courses/course_list.html', context)

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    lessons = course.lessons.all()
    reviews = course.reviews.select_related('user').order_by('-created_at')
    
    # Проверка, записан ли пользователь
    is_enrolled = False
    has_liked = False
    user_review = None
    
    if request.user.is_authenticated:
        is_enrolled = CourseEnrollment.objects.filter(user=request.user, course=course).exists()
        has_liked = CourseLike.objects.filter(user=request.user, course=course).exists()
        try:
            user_review = CourseReview.objects.get(user=request.user, course=course)
        except CourseReview.DoesNotExist:
            pass
    
    context = {
        'course': course,
        'lessons': lessons,
        'reviews': reviews,
        'is_enrolled': is_enrolled,
        'has_liked': has_liked,
        'user_review': user_review,
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
@require_POST
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    enrollment, created = CourseEnrollment.objects.get_or_create(
        user=request.user,
        course=course
    )
    
    if created:
        messages.success(request, f'Вы записались на курс "{course.title}"!')
    else:
        messages.info(request, f'Вы уже записаны на курс "{course.title}"')
    
    return redirect('courses:course_detail', course_id=course_id)

@login_required
@require_POST
def toggle_like(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    like, created = CourseLike.objects.get_or_create(
        user=request.user,
        course=course
    )
    
    if not created:
        like.delete()
        has_liked = False
    else:
        has_liked = True
    
    return JsonResponse({
        'success': True,
        'has_liked': has_liked,
        'likes_count': course.likes.count()
    })

@login_required
@require_POST
def submit_review(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    rating = int(request.POST.get('rating'))
    comment = request.POST.get('comment')
    
    review, created = CourseReview.objects.update_or_create(
        user=request.user,
        course=course,
        defaults={'rating': rating, 'comment': comment}
    )
    
    if created:
        messages.success(request, 'Ваш отзыв добавлен!')
    else:
        messages.success(request, 'Ваш отзыв обновлен!')
    
    return redirect('courses:course_detail', course_id=course_id)

@login_required
def lesson_view(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Проверка записи на курс
    is_enrolled = CourseEnrollment.objects.filter(user=request.user, course=course).exists()
    if not is_enrolled and not lesson.is_free:
        messages.error(request, 'Запишитесь на курс для доступа к урокам')
        return redirect('courses:course_detail', course_id=course_id)
    
    lessons = list(course.lessons.all().order_by('order'))
    current_index = lessons.index(lesson)
    
    prev_lesson = lessons[current_index - 1] if current_index > 0 else None
    next_lesson = lessons[current_index + 1] if current_index < len(lessons) - 1 else None
    
    # Обновление прогресса
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    if enrollment:
        completed_lessons = enrollment.completed_lessons.count() if hasattr(enrollment, 'completed_lessons') else 0
        total_lessons = lessons.count()
        enrollment.progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
        enrollment.save()
    
    context = {
        'course': course,
        'lesson': lesson,
        'all_lessons': lessons,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_enrolled': is_enrolled,
        'course_progress': enrollment.progress if enrollment else 0,
    }
    return render(request, 'courses/lesson_view.html', context)
