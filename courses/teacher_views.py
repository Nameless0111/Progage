from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.db.models import Count, Avg
from .models import Course, Lesson, Category, TestQuestion, TestAnswer, PracticeAssignment, CodeSubmission
from .forms import CourseForm, LessonForm, TestQuestionForm, TestAnswerFormSet, PracticeAssignmentForm, TestCaseForm

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    # Получаем курсы преподавателя
    courses = Course.objects.filter(instructor=request.user).select_related('category').prefetch_related('lessons', 'enrollments')
    
    # Статистика
    total_courses = courses.count()
    total_students = sum(course.enrollments.count() for course in courses)
    total_lessons = sum(course.lessons.count() for course in courses)
    avg_rating = courses.aggregate(avg_rating=Avg('reviews__rating'))['avg_rating'] or 0
    
    context = {
        'courses': courses,
        'total_courses': total_courses,
        'total_students': total_students,
        'total_lessons': total_lessons,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'courses/teacher/dashboard.html', context)

@login_required
def create_course(request):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, 'Курс успешно создан!')
            return redirect('courses:teacher_dashboard')
    else:
        form = CourseForm()
    
    categories = Category.objects.all()
    return render(request, 'courses/teacher/create_course.html', {
        'form': form,
        'categories': categories
    })

@login_required
def edit_course(request, course_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Курс успешно обновлен!')
            return redirect('courses:teacher_dashboard')
    else:
        form = CourseForm(instance=course)
    
    categories = Category.objects.all()
    return render(request, 'courses/teacher/edit_course.html', {
        'form': form,
        'course': course,
        'categories': categories
    })

@login_required
def delete_course(request, course_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Курс успешно удален!')
        return redirect('courses:teacher_dashboard')
    
    return render(request, 'courses/teacher/delete_course.html', {'course': course})

@login_required
def course_lessons(request, course_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    lessons = course.lessons.all().order_by('order')
    
    # Добавляем информацию о тестах и заданиях
    lesson_data = []
    for lesson in lessons:
        lesson_info = {
            'lesson': lesson,
            'has_test_questions': False,
            'test_question_count': 0,
            'has_practice_assignment': False,
            'practice_submission_count': 0,
        }
        
        # Проверяем наличие тестовых вопросов
        if lesson.lesson_type == 'test':
            from .models import TestQuestion
            test_questions = TestQuestion.objects.filter(lesson=lesson)
            lesson_info['has_test_questions'] = test_questions.exists()
            lesson_info['test_question_count'] = test_questions.count()
        
        # Проверяем наличие практического задания
        if lesson.lesson_type == 'practice':
            try:
                practice_assignment = lesson.practice_assignment
                lesson_info['has_practice_assignment'] = True
                lesson_info['practice_submission_count'] = practice_assignment.submissions.count()
            except:
                lesson_info['has_practice_assignment'] = False
        
        lesson_data.append(lesson_info)
    
    context = {
        'course': course,
        'lesson_data': lesson_data,
    }
    return render(request, 'courses/teacher/course_lessons.html', context)

@login_required
def create_lesson(request, course_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    # Получаем тип урока из параметра
    lesson_type = request.GET.get('type', 'lecture')
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            # Автоматически определяем порядок
            last_lesson = course.lessons.order_by('-order').first()
            lesson.order = (last_lesson.order + 1) if last_lesson else 1
            lesson.save()
            messages.success(request, 'Урок успешно создан!')
            
            # Перенаправляем в зависимости от типа урока
            if lesson.lesson_type == 'test':
                return redirect('courses:test_constructor', lesson_id=lesson.id)
            elif lesson.lesson_type == 'practice':
                return redirect('courses:practice_assignment', lesson_id=lesson.id)
            else:
                return redirect('courses:teacher_course_lessons', course_id=course.id)
    else:
        form = LessonForm(initial={'lesson_type': lesson_type})
    
    return render(request, 'courses/teacher/create_lesson.html', {
        'form': form,
        'course': course,
        'lesson_type': lesson_type
    })

@login_required
def edit_lesson(request, course_id, lesson_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'Урок успешно обновлен!')
            return redirect('courses:teacher_course_lessons', course_id=course.id)
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'courses/teacher/edit_lesson.html', {
        'form': form,
        'course': course,
        'lesson': lesson
    })

@login_required
def delete_lesson(request, course_id, lesson_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Урок успешно удален!')
        return redirect('courses:teacher_course_lessons', course_id=course.id)
    
    return render(request, 'courses/teacher/delete_lesson.html', {
        'course': course,
        'lesson': lesson
    })

@login_required
def test_constructor(request, lesson_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    
    if lesson.lesson_type != 'test':
        messages.error(request, 'Конструктор тестов доступен только для уроков типа "Тест"')
        return redirect('courses:edit_lesson', lesson.course.id, lesson.id)
    
    if request.method == 'POST':
        # Обработка добавления нового вопроса
        question_form = TestQuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.lesson = lesson
            # Устанавливаем порядок
            max_order = TestQuestion.objects.filter(lesson=lesson).aggregate(
                models.Max('order'))['order__max'] or 0
            question.order = max_order + 1
            question.save()
            
            # Обрабатываем ответы
            answers = request.POST.getlist('answers[]')
            correct_answer = request.POST.get('correct_answer')
            correct_answers = request.POST.getlist('correct_answers[]')
            
            for i, answer_text in enumerate(answers):
                if answer_text.strip():  # Пропускаем пустые ответы
                    answer = TestAnswer.objects.create(
                        question=question,
                        answer_text=answer_text.strip(),
                        is_correct=(
                            str(i) == correct_answer or  # Для одиночного выбора
                            str(i) in correct_answers     # Для множественного выбора
                        )
                    )
            
            messages.success(request, 'Вопрос добавлен!')
            return redirect('courses:test_constructor', lesson_id=lesson.id)
    else:
        question_form = TestQuestionForm()
    
    questions = TestQuestion.objects.filter(lesson=lesson).prefetch_related('answers')
    
    # Добавляем статистику
    total_points = sum(question.points for question in questions)
    question_types = list(set(question.question_type for question in questions))
    
    context = {
        'lesson': lesson,
        'course': lesson.course,
        'question_form': question_form,
        'questions': questions,
        'total_points': total_points,
        'question_types': question_types,
    }
    return render(request, 'courses/teacher/test_constructor.html', context)

@login_required
def edit_test_question(request, lesson_id, question_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    question = get_object_or_404(TestQuestion, id=question_id, lesson=lesson)
    
    if request.method == 'POST':
        question_form = TestQuestionForm(request.POST, instance=question)
        answer_formset = TestAnswerFormSet(request.POST, instance=question)
        
        if question_form.is_valid() and answer_formset.is_valid():
            question_form.save()
            answer_formset.save()
            messages.success(request, 'Вопрос обновлен!')
            return redirect('courses:test_constructor', lesson_id=lesson.id)
    else:
        question_form = TestQuestionForm(instance=question)
        answer_formset = TestAnswerFormSet(instance=question)
    
    context = {
        'lesson': lesson,
        'course': lesson.course,
        'question': question,
        'question_form': question_form,
        'answer_formset': answer_formset,
    }
    return render(request, 'courses/teacher/edit_test_question.html', context)

@login_required
def delete_test_question(request, lesson_id, question_id):
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    question = get_object_or_404(TestQuestion, id=question_id, lesson=lesson)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Вопрос удален!')
        return redirect('courses:test_constructor', lesson_id=lesson.id)
    
    return render(request, 'courses/teacher/delete_test_question.html', {
        'lesson': lesson,
        'course': lesson.course,
        'question': question
    })

@login_required
def practice_assignment(request, lesson_id):
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== practice_assignment view called ===")
    logger.info(f"lesson_id: {lesson_id}")
    logger.info(f"user: {request.user}")
    logger.info(f"method: {request.method}")
    
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')

    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    logger.info(f"lesson found: {lesson.title} (type: {lesson.lesson_type})")
    
    try:
        assignment = lesson.practice_assignment
        logger.info(f"existing assignment found: {assignment}")
    except PracticeAssignment.DoesNotExist:
        assignment = None
        logger.info(f"no existing assignment")
    
    if request.method == 'POST':
        form = PracticeAssignmentForm(request.POST, instance=assignment)
        
        if not form.is_valid():
            logger.error(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                logger.error(f"  {field}: {errors}")
        
        if form.is_valid():
            logger.info(f"Form is valid, saving...")
            
            # Сохраняем форму (она сама разберется с новым/существующим объектом)
            assignment = form.save(commit=False)
            
            # Устанавливаем lesson если это новый объект
            if not assignment.id:
                assignment.lesson = lesson
                logger.info(f"New assignment, setting lesson: {lesson}")
            else:
                logger.info(f"Updating existing assignment: {assignment.id}")
            
            logger.info(f"Assignment before test processing: {assignment}")
            
            # Обработка тестовых случаев (для всех типов проверки)
            test_cases = []
            
            # Собираем все тестовые случаи с индексами
            i = 0
            while True:
                input_key = f'test_input_{i}'
                output_key = f'test_output_{i}'
                
                if output_key not in request.POST:
                    break  # Больше нет тестов
                
                input_data = request.POST.get(input_key, '').strip()
                output_data = request.POST.get(output_key, '').strip()
                
                # Сохраняем только если есть выходные данные
                if output_data:
                    test_cases.append({
                        'input': input_data,
                        'expected_output': output_data
                    })
                
                i += 1
            
            # Всегда сохраняем тестовые случаи (пустой список если нет)
            assignment.test_cases = test_cases
            
            try:
                assignment.save()  # Сохраняем с тестами
                logger.info(f"Assignment saved successfully: ID {assignment.id}")
            except Exception as e:
                logger.error(f"Error saving assignment: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            messages.success(request, 'Практическое задание сохранено')
            logger.info(f"Redirecting to teacher_course_lessons for course {lesson.course.id}")
            return redirect('courses:teacher_course_lessons', lesson.course.id)
    else:
        logger.info(f"GET request received")
        form = PracticeAssignmentForm(instance=assignment)
        logger.info(f"Form created for GET: {form}")
    
    # Получаем тестовые случаи
    test_cases = assignment.test_cases if assignment else []
    logger.info(f"Test cases loaded: {len(test_cases)}")
    
    # Вычисляем статистику
    total_submissions = 0
    correct_submissions = 0
    unique_students = 0
    
    if assignment:
        total_submissions = assignment.submissions.count()
        correct_submissions = assignment.submissions.filter(is_correct=True).count()
        unique_students = assignment.submissions.values('user').distinct().count()
    
    context = {
        'course': lesson.course,
        'lesson': lesson,
        'form': form,
        'assignment': assignment,
        'test_cases': test_cases,
        'total_submissions': total_submissions,
        'correct_submissions': correct_submissions,
        'unique_students': unique_students,
    }
    
    logger.info(f"Rendering template with context keys: {list(context.keys())}")
    # Выбираем шаблон в зависимости от типа проверки
    if assignment and assignment.require_manual_review:
        return render(request, 'courses/teacher/practice_assignment_manual.html', context)
    else:
        return render(request, 'courses/teacher/practice_assignment.html', context)

@login_required
def practice_assignment_manual(request, lesson_id):
    """Создание и редактирование практического задания с ручной проверкой"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')

    lesson = get_object_or_404(Lesson, id=lesson_id, course__instructor=request.user)
    
    try:
        assignment = lesson.practice_assignment
    except PracticeAssignment.DoesNotExist:
        assignment = None
    
    if request.method == 'POST':
        form = PracticeAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.lesson = lesson
            assignment.require_manual_review = True  # Принудительно включаем ручную проверку
            
            # Обработка тестовых случаев
            test_cases = []
            
            # Собираем все тестовые случаи с индексами
            i = 0
            while True:
                input_key = f'test_input_{i}'
                output_key = f'test_output_{i}'
                
                if output_key not in request.POST:
                    break  # Больше нет тестов
                
                input_data = request.POST.get(input_key, '').strip()
                output_data = request.POST.get(output_key, '').strip()
                
                if output_data:  # Сохраняем только если есть выходные данные
                    test_cases.append({
                        'input': input_data,
                        'expected_output': output_data
                    })
                
                i += 1
            
            assignment.test_cases = test_cases
            
            assignment.save()  # Только один save
            
            messages.success(request, 'Практическое задание сохранено')
            return redirect('courses:teacher_course_lessons', lesson.course.id)
    else:
        form = PracticeAssignmentForm(instance=assignment)
        if not assignment:
            form.initial['require_manual_review'] = True
    
    # Вычисляем статистику для ручной проверки
    total_submissions = 0
    approved_submissions = 0
    rejected_submissions = 0
    pending_submissions = 0
    unique_students = 0
    
    if assignment:
        total_submissions = assignment.submissions.count()
        approved_submissions = assignment.submissions.filter(status='approved').count()
        rejected_submissions = assignment.submissions.filter(status='rejected').count()
        pending_submissions = assignment.submissions.filter(status='pending').count()
        unique_students = assignment.submissions.values('user').distinct().count()
        
        # Вычисляем среднюю оценку
        graded_submissions = assignment.submissions.filter(grade__isnull=False)
        if graded_submissions.exists():
            avg_grade = graded_submissions.aggregate(avg=models.Avg('grade'))['avg'] or 0
        else:
            avg_grade = 0
    
    # Получаем тестовые случаи
    test_cases = assignment.test_cases if assignment else []
    
    context = {
        'course': lesson.course,
        'lesson': lesson,
        'form': form,
        'assignment': assignment,
        'test_cases': test_cases,
        'total_submissions': total_submissions,
        'approved_submissions': approved_submissions,
        'rejected_submissions': rejected_submissions,
        'pending_submissions': pending_submissions,
        'unique_students': unique_students,
        'avg_grade': avg_grade if assignment else 0,
    }
    
    return render(request, 'courses/teacher/practice_assignment_manual.html', context)

@login_required
def review_submission(request, submission_id):
    """Проверка отправки кода"""
    if request.user.role != 'teacher':
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')

    submission = get_object_or_404(CodeSubmission, id=submission_id)
    
    # Проверяем, что преподаватель имеет доступ к этому заданию
    if submission.assignment.lesson.course.instructor != request.user:
        messages.error(request, 'У вас нет доступа к этому заданию')
        return redirect('courses:teacher_dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')
        grade_value = None

        if grade:
            try:
                grade_value = int(grade)
            except (TypeError, ValueError):
                messages.error(request, 'Оценка должна быть числом')
                return redirect('courses:review_submission', submission_id=submission.id)

            if grade_value < 0 or grade_value > submission.assignment.max_grade:
                messages.error(request, f'Оценка должна быть от 0 до {submission.assignment.max_grade}')
                return redirect('courses:review_submission', submission_id=submission.id)
        
        # Обновляем данные проверки
        submission.grade = grade_value
        submission.feedback = feedback
        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        
        # Обновляем статус в зависимости от действия
        if action == 'approve':
            submission.status = 'approved'
            messages.success(request, 'Работа принята')
        elif action == 'reject':
            submission.status = 'rejected'
            messages.success(request, 'Работа отклонена')
        elif action == 'save':
            submission.status = 'reviewed'
            # Не показываем сообщение при автосохранении
        
        submission.save()
        
        if action != 'save':
            return redirect('courses:practice_assignment_manual', submission.assignment.lesson.id)
    
    context = {
        'submission': submission,
        'assignment': submission.assignment,
    }
    
    return render(request, 'courses/teacher/review_submission.html', context)

@login_required
def submit_code(request, lesson_id):
    """Отправка кода на проверку"""
    if not request.user.is_authenticated:
        messages.error(request, 'Необходимо авторизоваться')
        return redirect('accounts:login')
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if lesson.lesson_type != 'practice':
        messages.error(request, 'Этот урок не является практическим заданием')
        return redirect('courses:lesson_view', lesson.course.id, lesson.id)
    
    assignment = get_object_or_404(PracticeAssignment, lesson=lesson)
    
    if not assignment.is_published:
        messages.error(request, 'Задание еще не опубликовано')
        return redirect('courses:lesson_view', lesson.course.id, lesson.id)
    
    # Проверяем лимит попыток
    attempt_count = CodeSubmission.objects.filter(
        assignment=assignment, 
        user=request.user
    ).count()
    
    if attempt_count >= assignment.max_attempts:
        messages.error(request, f'Исчерпан лимит попыток ({assignment.max_attempts})')
        return redirect('courses:lesson_view', lesson.course.id, lesson.id)
    
    if request.method == 'POST':
        from .compiler_service import compiler
        
        code = request.POST.get('code', '')
        
        if not code.strip():
            messages.error(request, 'Код не может быть пустым')
            return redirect('courses:lesson_view', lesson.course.id, lesson.id)
        
        # Создаем отправку
        attempt_number = attempt_count + 1
        submission = CodeSubmission.objects.create(
            assignment=assignment,
            user=request.user,
            code=code,
            programming_language=assignment.programming_language,
            attempt_number=attempt_number,
            status='running'
        )
        
        # Выполняем код
        test_cases = assignment.test_cases if isinstance(assignment.test_cases, list) else []
        if not test_cases and assignment.test_cases:
            test_cases = assignment.test_cases
        
        if test_cases:
            # Запускаем на тестовых случаях
            results = compiler.run_test_cases(code, assignment.programming_language, test_cases)
            
            # Обновляем отправку
            submission.status = results['overall_status']
            submission.test_cases_passed = results['passed_tests']
            submission.total_test_cases = results['total_tests']
            submission.is_correct = results['overall_status'] == 'success'
            submission.executed_at = timezone.now()
            
            # Сохраняем детали тестов
            if results['test_results']:
                test_output = []
                for test_result in results['test_results']:
                    test_output.append(f"Тест {test_result['test_number']}: {'пройден' if test_result['passed'] else 'не пройден'}")
                    if not test_result['passed']:
                        test_output.append(f"  Ввод: {test_result['input']}")
                        test_output.append(f"  Ожидаемый: {test_result['expected_output']}")
                        test_output.append(f"  Полученный: {test_result['actual_output']}")
                submission.output = '\n'.join(test_output)
        else:
            # Простое выполнение без тестов
            result = compiler.compile_and_run(code, assignment.programming_language)
            submission.status = result['status']
            submission.output = result.get('stdout', '') + result.get('stderr', '')
            submission.execution_time = result.get('execution_time')
            submission.is_correct = result['success']
            submission.executed_at = timezone.now()
        
        submission.save()
        
        # Сообщение о результате
        if submission.is_correct:
            messages.success(request, 'Решение верное. Все тесты пройдены.')
        else:
            messages.warning(request, f'Решение неверное. Пройдено {submission.test_cases_passed} из {submission.total_test_cases} тестов.')
        
        return redirect('courses:lesson_view', lesson.course.id, lesson.id)
    
    return redirect('courses:lesson_view', lesson.course.id, lesson.id)
