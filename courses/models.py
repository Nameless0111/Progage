from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from urllib.parse import quote
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Преподаватель')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='Категория')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner', verbose_name='Уровень')
    programming_language = models.CharField(max_length=50, blank=True, default='', verbose_name='Язык программирования')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Цена')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True, verbose_name='Превью')
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    
    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

    @property
    def thumbnail_url(self):
        fallback = f"https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1200&auto=format&fit=crop&q=60&sig={quote(self.title)}"

        if not self.thumbnail or not getattr(self.thumbnail, "name", None):
            return fallback

        try:
            if not self.thumbnail.storage.exists(self.thumbnail.name):
                return fallback
        except Exception:
            pass

        try:
            return self.thumbnail.url
        except Exception:
            return fallback
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    @property
    def enrollment_count(self):
        return self.enrollments.count()
    
    @property
    def lesson_count(self):
        return self.lessons.count()

class Lesson(models.Model):
    LESSON_TYPES = [
        ('lecture', 'Лекция'),
        ('test', 'Тест'),
        ('practice', 'Практическое задание'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name='Курс')
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='lecture', verbose_name='Тип урока')
    content = models.TextField(verbose_name='Содержание лекции', blank=True, help_text='Текстовое содержание для лекции')
    attachment = models.FileField(upload_to='lesson_attachments/', null=True, blank=True, verbose_name='Прикрепленный файл', help_text='Видео, презентация, PDF, Word и другие файлы')
    attachment_name = models.CharField(max_length=255, blank=True, verbose_name='Название файла')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_free = models.BooleanField(default=False, verbose_name='Бесплатный')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    
    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def file_extension(self):
        """Возвращает расширение файла"""
        if self.attachment:
            return self.attachment.name.split('.')[-1].lower()
        return None
    
    @property
    def file_type(self):
        """Определяет тип файла"""
        if not self.attachment:
            return None
        
        ext = self.file_extension
        if ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']:
            return 'video'
        elif ext in ['pdf']:
            return 'pdf'
        elif ext in ['doc', 'docx']:
            return 'word'
        elif ext in ['ppt', 'pptx']:
            return 'presentation'
        elif ext in ['zip', 'rar', '7z']:
            return 'archive'
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            return 'image'
        else:
            return 'document'
    
    @property
    def icon_class(self):
        """Возвращает иконку для типа файла"""
        file_type = self.file_type
        if file_type == 'video':
            return 'fas fa-video'
        elif file_type == 'pdf':
            return 'fas fa-file-pdf'
        elif file_type == 'word':
            return 'fas fa-file-word'
        elif file_type == 'presentation':
            return 'fas fa-file-powerpoint'
        elif file_type == 'archive':
            return 'fas fa-file-archive'
        elif file_type == 'image':
            return 'fas fa-file-image'
        else:
            return 'fas fa-file-alt'
    
    def save(self, *args, **kwargs):
        """При сохранении устанавливает название файла"""
        if self.attachment and not self.attachment_name:
            self.attachment_name = self.attachment.name.split('/')[-1]
        super().save(*args, **kwargs)

class TestQuestion(models.Model):
    QUESTION_TYPES = [
        ('single', 'Один вариант ответа'),
        ('multiple', 'Несколько вариантов ответа'),
        ('text', 'Свободный текстовый ответ'),
        ('essay', 'Развернутый ответ с проверкой'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='test_questions', verbose_name='Урок')
    question_text = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, verbose_name='Тип вопроса')
    points = models.PositiveIntegerField(default=1, verbose_name='Баллы за вопрос')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    explanation = models.TextField(blank=True, verbose_name='Пояснение к ответу')
    is_required = models.BooleanField(default=True, verbose_name='Обязательный вопрос')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Вопрос теста'
        verbose_name_plural = 'Вопросы теста'
        ordering = ['order']
    
    def __str__(self):
        return f"Вопрос {self.order}: {self.question_text[:50]}..."

class TestAnswer(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    answer_text = models.CharField(max_length=500, verbose_name='Текст ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.answer_text[:30]}... ({'правильный' if self.is_correct else 'неправильный'})"

class TestSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Студент')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name='Урок')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата сдачи')
    score = models.PositiveIntegerField(default=0, verbose_name='Набранные баллы')
    max_score = models.PositiveIntegerField(verbose_name='Максимальные баллы')
    percentage = models.FloatField(verbose_name='Процент выполнения')
    is_completed = models.BooleanField(default=False, verbose_name='Завершен')
    needs_review = models.BooleanField(default=False, verbose_name='Требует проверки')
    
    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({self.percentage}%)"
    
    def save(self, *args, **kwargs):
        if self.max_score > 0:
            self.percentage = (self.score / self.max_score) * 100
        super().save(*args, **kwargs)

class TestAnswerSubmission(models.Model):
    submission = models.ForeignKey(TestSubmission, on_delete=models.CASCADE, related_name='answer_submissions', verbose_name='Результат теста')
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, verbose_name='Вопрос')
    
    # Для вариантов ответа
    selected_answers = models.ManyToManyField(TestAnswer, blank=True, verbose_name='Выбранные варианты')
    
    # Для текстовых ответов
    text_answer = models.TextField(blank=True, verbose_name='Текстовый ответ')
    
    # Оценка ответа
    score = models.PositiveIntegerField(default=0, verbose_name='Баллы')
    is_correct = models.BooleanField(default=False, verbose_name='Правильно')
    feedback = models.TextField(blank=True, verbose_name='Обратная связь')
    needs_review = models.BooleanField(default=False, verbose_name='Требует проверки')
    
    class Meta:
        verbose_name = 'Ответ на вопрос'
        verbose_name_plural = 'Ответы на вопросы'
        unique_together = ['submission', 'question']
    
    def __str__(self):
        return f"Ответ на вопрос {self.question.order} от {self.submission.user.username}"

class PracticeAssignment(models.Model):
    """Практическое задание"""
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
    ]
    
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='practice_assignment', verbose_name='Урок')
    title = models.CharField(max_length=200, verbose_name='Название задания')
    description = models.TextField(verbose_name='Описание задания')
    requirements = models.TextField(verbose_name='Требования к решению')
    programming_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, verbose_name='Язык программирования')
    starter_code = models.TextField(blank=True, verbose_name='Начальный код')
    solution_code = models.TextField(blank=True, verbose_name='Код решения (для проверки)')
    expected_output = models.TextField(blank=True, verbose_name='Ожидаемый вывод')
    test_cases = models.JSONField(default=list, verbose_name='Тестовые случаи')
    time_limit = models.PositiveIntegerField(default=5, verbose_name='Лимит времени (секунды)')
    memory_limit = models.PositiveIntegerField(default=256, verbose_name='Лимит памяти (МБ)')
    max_attempts = models.PositiveIntegerField(default=10, verbose_name='Максимум попыток')
    max_grade = models.PositiveIntegerField(default=100, verbose_name='Максимальная оценка')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн')
    require_manual_review = models.BooleanField(default=False, verbose_name='Требуется ручная проверка')
    is_published = models.BooleanField(default=False, verbose_name='Опубликовано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    
    class Meta:
        verbose_name = 'Практическое задание'
        verbose_name_plural = 'Практические задания'
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"

class CodeSubmission(models.Model):
    """Отправка кода на проверку"""
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('running', 'Выполняется'),
        ('success', 'Успешно'),
        ('error', 'Ошибка'),
        ('timeout', 'Превышен лимит времени'),
        ('memory', 'Превышен лимит памяти'),
        ('wrong', 'Неверный ответ'),
        ('approved', 'Принято'),
        ('rejected', 'Отклонено'),
        ('reviewed', 'Проверено'),
    ]
    
    assignment = models.ForeignKey(PracticeAssignment, on_delete=models.CASCADE, related_name='submissions', verbose_name='Задание')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Студент')
    code = models.TextField(verbose_name='Код решения')
    programming_language = models.CharField(max_length=20, verbose_name='Язык программирования')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    output = models.TextField(blank=True, verbose_name='Вывод программы')
    error_message = models.TextField(blank=True, verbose_name='Сообщение об ошибке')
    execution_time = models.FloatField(blank=True, null=True, verbose_name='Время выполнения (сек)')
    memory_used = models.PositiveIntegerField(blank=True, null=True, verbose_name='Использовано памяти (МБ)')
    test_cases_passed = models.PositiveIntegerField(default=0, verbose_name='Пройдено тестов')
    total_test_cases = models.PositiveIntegerField(default=0, verbose_name='Всего тестов')
    attempt_number = models.PositiveIntegerField(default=1, verbose_name='Номер попытки')
    is_correct = models.BooleanField(default=False, verbose_name='Решено верно')
    
    # Поля для ручной проверки
    grade = models.PositiveIntegerField(null=True, blank=True, verbose_name='Оценка')
    feedback = models.TextField(blank=True, verbose_name='Комментарий преподавателя')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions', verbose_name='Проверил')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Время проверки')
    
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')
    executed_at = models.DateTimeField(blank=True, null=True, verbose_name='Выполнено')
    
    class Meta:
        verbose_name = 'Отправка кода'
        verbose_name_plural = 'Отправки кода'
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'user', 'attempt_number']
    
    def __str__(self):
        return f"{self.user.username} - {self.assignment.title} (Попытка {self.attempt_number})"

class SecurityConfig(models.Model):
    """Конфигурация безопасности компилятора"""
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
    ]
    
    programming_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, unique=True, verbose_name='Язык программирования')
    is_enabled = models.BooleanField(default=True, verbose_name='Включен')
    compile_command = models.CharField(max_length=200, verbose_name='Команда компиляции')
    run_command = models.CharField(max_length=200, verbose_name='Команда запуска')
    file_extension = models.CharField(max_length=10, verbose_name='Расширение файла')
    max_execution_time = models.PositiveIntegerField(default=10, verbose_name='Макс. время выполнения (сек)')
    max_memory = models.PositiveIntegerField(default=512, verbose_name='Макс. память (МБ)')
    allowed_libraries = models.JSONField(default=list, verbose_name='Разрешенные библиотеки')
    forbidden_patterns = models.JSONField(default=list, verbose_name='Запрещенные паттерны кода')
    docker_image = models.CharField(max_length=200, blank=True, verbose_name='Docker образ')
    security_level = models.CharField(max_length=20, choices=[
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('maximum', 'Максимальный'),
    ], default='high', verbose_name='Уровень безопасности')
    
    class Meta:
        verbose_name = 'Конфигурация безопасности'
        verbose_name_plural = 'Конфигурации безопасности'
    
    def __str__(self):
        return f"{self.get_programming_language_display()} - {self.get_security_level_display()}"

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Курс')
    is_active = models.BooleanField(default=True, verbose_name='Активная запись')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата завершения')
    progress = models.PositiveIntegerField(default=0, verbose_name='Прогресс (%)')
    completed_lessons = models.ManyToManyField(Lesson, blank=True, verbose_name='Завершенные уроки')
    
    class Meta:
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class CourseLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='likes', verbose_name='Курс')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    
    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.username} лайкнул {self.course.title}"

class CourseReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', verbose_name='Курс')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Рейтинг'
    )
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"Отзыв {self.user.username} на {self.course.title}"


class LessonComment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments', verbose_name='Урок')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    content = models.TextField(verbose_name='Содержание комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Комментарий к уроку'
        verbose_name_plural = 'Комментарии к урокам'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Комментарий {self.user.username} к уроку {self.lesson.title}"




