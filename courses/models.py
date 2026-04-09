from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from urllib.parse import quote

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
    title = models.CharField(max_length=200, verbose_name='Название')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name='Курс')
    content = models.TextField(verbose_name='Содержание')
    video_url = models.URLField(blank=True, verbose_name='URL видео')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_free = models.BooleanField(default=False, verbose_name='Бесплатный')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Курс')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата завершения')
    progress = models.PositiveIntegerField(default=0, verbose_name='Прогресс (%)')
    
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
