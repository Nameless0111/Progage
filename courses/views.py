from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
from django.urls import reverse
from django.utils import timezone
from .models import (
    Course, Lesson, CourseEnrollment, CourseLike, CourseReview, Category, 
    PracticeAssignment, CodeSubmission, TestQuestion, TestAnswer, TestSubmission, 
    TestAnswerSubmission
)

def course_list(request):
    courses = Course.objects.filter(is_published=True).select_related('instructor', 'category').prefetch_related('likes', 'reviews')
    categories = Category.objects.all()
    
    # Поиск и фильтрация
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category')
    level = request.GET.get('level')
    
    # Поиск по названию
    if search_query:
        courses = courses.filter(title__icontains=search_query)
    
    # Фильтрация по категории
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    # Фильтрация по уровню
    if level:
        courses = courses.filter(level=level)
    
    # Получаем популярные курсы (топ 5 по лайкам)
    popular_courses = Course.objects.filter(is_published=True).annotate(
        like_count=models.Count('likes')
    ).order_by('-like_count')[:5]
    
    context = {
        'courses': courses,
        'categories': categories,
        'popular_courses': popular_courses,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_level': level,
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
    comment = request.POST.get('comment', '').strip()

    try:
        rating = int(request.POST.get('rating', ''))
    except (TypeError, ValueError):
        messages.error(request, 'Выберите оценку от 1 до 5')
        return redirect('courses:course_detail', course_id=course_id)

    if rating < 1 or rating > 5:
        messages.error(request, 'Оценка должна быть от 1 до 5')
        return redirect('courses:course_detail', course_id=course_id)

    if not comment:
        messages.error(request, 'Комментарий не может быть пустым')
        return redirect('courses:course_detail', course_id=course_id)
    
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
    if not is_enrolled:
        messages.error(request, 'Запишитесь на курс для доступа к урокам')
        return redirect('courses:course_detail', course_id=course_id)
    
    lessons = list(course.lessons.all().order_by('order'))
    current_index = lessons.index(lesson)
    
    prev_lesson = lessons[current_index - 1] if current_index > 0 else None
    next_lesson = lessons[current_index + 1] if current_index < len(lessons) - 1 else None
    
    # Обновление прогресса (временно не используем completed_lessons)
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    # TODO: Добавить отслеживание завершенных уроков после создания миграций
    
    # Получаем данные о практическом задании и отправках студента
    user_submissions = []
    if lesson.lesson_type == 'practice':
        try:
            assignment = PracticeAssignment.objects.get(lesson=lesson)
            user_submissions = CodeSubmission.objects.filter(
                assignment=assignment, 
                user=request.user
            ).order_by('-submitted_at')
        except PracticeAssignment.DoesNotExist:
            pass
    
    # Вычисляем общую сумму баллов за тест
    total_points = 0
    required_questions_count = 0
    has_correct_submission = False
    
    if lesson.lesson_type == 'test':
        total_points = sum(question.points or 0 for question in lesson.test_questions.all())
        required_questions_count = lesson.test_questions.filter(is_required=True).count()
    elif lesson.lesson_type == 'practice':
        has_correct_submission = user_submissions.filter(is_correct=True).exists() if user_submissions else False

    comments = lesson.comments.select_related('user', 'user__privacy_settings').all()
    
    context = {
        'course': course,
        'lesson': lesson,
        'all_lessons': lessons,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_enrolled': is_enrolled,
        'course_progress': enrollment.progress if enrollment else 0,
        'comments': comments,
        'user_submissions': user_submissions,
        'total_points': total_points,
        'required_questions_count': required_questions_count,
        'has_correct_submission': has_correct_submission,
    }
    return render(request, 'courses/lesson_view.html', context)

@login_required
def take_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if lesson.lesson_type != 'test':
        messages.error(request, 'Этот урок не является тестом')
        return redirect('courses:lesson_view', lesson.course.id, lesson.id)
    
    # Проверяем, записан ли студент на курс
    if not CourseEnrollment.objects.filter(user=request.user, course=lesson.course).exists():
        messages.error(request, 'Вы не записаны на этот курс')
        return redirect('courses:lesson_view', lesson.course.id, lesson.id)
    
    # Получаем вопросы теста
    questions = lesson.test_questions.all().prefetch_related('answers')
    
    if not questions.exists():
        messages.error(request, 'Тест еще не готов. Нет вопросов.')
        return redirect('courses:lesson_view', lesson.course.id, lesson.id)
    
    # Проверяем, не проходил ли студент уже этот тест
    existing_submission = TestSubmission.objects.filter(
        lesson=lesson, 
        user=request.user
    ).first()
    
    if existing_submission:
        messages.info(request, 'Вы уже проходили этот тест')
        return redirect('courses:test_result', lesson_id=lesson.id, submission_id=existing_submission.id)
    
    context = {
        'lesson': lesson,
        'course': lesson.course,
        'questions': questions,
        'total_points': sum(q.points or 0 for q in questions),
        'required_count': questions.filter(is_required=True).count(),
    }
    
    return render(request, 'courses/take_test.html', context)

@login_required
def submit_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if lesson.lesson_type != 'test':
        return JsonResponse({'error': 'Это не тест'}, status=400)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    if not CourseEnrollment.objects.filter(user=request.user, course=lesson.course, is_active=True).exists():
        return JsonResponse({'error': 'Вы не записаны на этот курс'}, status=403)
    
    # Получаем вопросы
    questions = lesson.test_questions.all()
    if not questions.exists():
        return JsonResponse({'error': 'В тесте пока нет вопросов'}, status=400)

    existing_submission = TestSubmission.objects.filter(lesson=lesson, user=request.user).first()
    if existing_submission:
        return JsonResponse({
            'success': True,
            'already_submitted': True,
            'score': existing_submission.score,
            'total_points': existing_submission.max_score,
            'percentage': int(
                (existing_submission.score / existing_submission.max_score * 100)
                if existing_submission.max_score > 0 else 0
            ),
            'redirect_url': reverse(
                'courses:test_result',
                kwargs={'lesson_id': lesson.id, 'submission_id': existing_submission.id}
            )
        })
    
    # Создаем submission
    max_score = sum(q.points or 0 for q in questions)
    submission = TestSubmission.objects.create(
        lesson=lesson,
        user=request.user,
        max_score=max_score,
        score=0,
        is_completed=True
    )
    
    # Обрабатываем ответы
    score = 0
    for question in questions:
        if question.question_type == 'single':
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                try:
                    answer = TestAnswer.objects.get(id=answer_id, question=question)
                    answer_submission = TestAnswerSubmission.objects.create(
                        submission=submission,
                        question=question,
                        score=question.points or 0,
                        is_correct=answer.is_correct,
                        needs_review=False
                    )
                    answer_submission.selected_answers.add(answer)
                    if answer.is_correct:
                        score += question.points or 0
                except TestAnswer.DoesNotExist:
                    pass
                    
        elif question.question_type == 'multiple':
            answer_ids = request.POST.getlist(f'question_{question.id}')
            correct_answers = question.answers.filter(is_correct=True)
            selected_answers = question.answers.filter(id__in=answer_ids)
            
            answer_submission = TestAnswerSubmission.objects.create(
                submission=submission,
                question=question,
                score=0,
                is_correct=False,
                needs_review=False
            )
            answer_submission.selected_answers.add(*selected_answers)
            
            # Проверяем правильность для множественного выбора
            if (set(selected_answers) == set(correct_answers) and 
                len(selected_answers) == len(correct_answers)):
                answer_submission.is_correct = True
                answer_submission.score = question.points or 0
                answer_submission.save()
                score += question.points or 0
                
        elif question.question_type == 'text':
            text_answer = request.POST.get(f'question_{question.id}', '')
            TestAnswerSubmission.objects.create(
                submission=submission,
                question=question,
                text_answer=text_answer.strip(),
                score=0,
                is_correct=False,
                needs_review=True  # Текстовые ответы требуют проверки
            )
            # Для текстовых ответов нужно ручная проверка
            pass
        elif question.question_type == 'essay':
            text_answer = request.POST.get(f'question_{question.id}', '')
            TestAnswerSubmission.objects.create(
                submission=submission,
                question=question,
                text_answer=text_answer.strip(),
                score=0,
                is_correct=False,
                needs_review=True
            )
    
    # Обновляем оценку
    submission.score = score
    submission.save()
    
    # Отмечаем урок как пройденный
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=lesson.course).first()
    if enrollment:
        enrollment.completed_lessons.add(lesson)
        # Обновляем прогресс
        total_lessons = lesson.course.lessons.count()
        completed_lessons = enrollment.completed_lessons.count()
        enrollment.progress = int((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0)
        enrollment.save()
    
    return JsonResponse({
        'success': True,
        'score': score,
        'total_points': submission.max_score,
        'percentage': int((score / submission.max_score * 100) if submission.max_score > 0 else 0),
        'redirect_url': reverse('courses:test_result', kwargs={'lesson_id': lesson.id, 'submission_id': submission.id})
    })

@login_required
def test_result(request, lesson_id, submission_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    submission = get_object_or_404(TestSubmission, id=submission_id, lesson=lesson, user=request.user)
    
    # Получаем ответы студента
    submission_answers = submission.answer_submissions.all().select_related('question')
    
    # Группируем ответы по вопросам
    answers_by_question = {}
    for answer in submission_answers:
        answers_by_question[answer.question.id] = answer
    
    context = {
        'lesson': lesson,
        'course': lesson.course,
        'submission': submission,
        'questions': lesson.test_questions.all().prefetch_related('answers'),
        'answers_by_question': answers_by_question,
        'percentage': int((submission.score / submission.max_score * 100) if submission.max_score > 0 else 0),
        'passed': submission.score >= (submission.max_score * 0.6)  # 60% для сдачи
    }
    
    return render(request, 'courses/test_result.html', context)

@login_required
@require_POST
def complete_lesson(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Проверка записи на курс
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'Запишитесь на курс для отслеживания прогресса')
        return redirect('courses:lesson_view', course_id=course_id, lesson_id=lesson_id)
    
    # Добавляем урок в завершенные
    enrollment.completed_lessons.add(lesson)
    
    # Обновляем прогресс
    total_lessons = course.lessons.count()
    completed_lessons = enrollment.completed_lessons.count()
    enrollment.progress = int((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0)
    enrollment.save()
    
    messages.success(request, f'Урок "{lesson.title}" отмечен как пройденный!')
    
    return redirect('courses:lesson_view', course_id=course_id, lesson_id=lesson_id)

@login_required
@require_POST
def add_comment(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Проверка записи на курс
    enrollment = CourseEnrollment.objects.filter(user=request.user, course=course).first()
    if not enrollment:
        messages.error(request, 'Запишитесь на курс для добавления комментариев')
        return redirect('courses:lesson_view', course_id=course_id, lesson_id=lesson_id)
    
    content = request.POST.get('content', '').strip()
    if content:
        from .models import LessonComment
        LessonComment.objects.create(
            lesson=lesson,
            user=request.user,
            content=content
        )
        messages.success(request, 'Комментарий добавлен!')
    else:
        messages.error(request, 'Комментарий не может быть пустым')
    
    return redirect('courses:lesson_view', course_id=course_id, lesson_id=lesson_id)
