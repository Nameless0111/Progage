from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from courses.models import Course, CourseEnrollment, Lesson
import json

User = get_user_model()


class ActivityLog(models.Model):
    """Лог активности пользователей"""
    ACTION_TYPES = [
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('view_course', 'Просмотр курса'),
        ('enroll_course', 'Запись на курс'),
        ('complete_lesson', 'Завершение урока'),
        ('start_lesson', 'Начало урока'),
        ('submit_assignment', 'Сдача задания'),
        ('view_profile', 'Просмотр профиля'),
        ('update_profile', 'Обновление профиля'),
        ('create_course', 'Создание курса'),
        ('update_course', 'Обновление курса'),
        ('delete_course', 'Удаление курса'),
        ('create_lesson', 'Создание урока'),
        ('update_lesson', 'Обновление урока'),
        ('delete_lesson', 'Удаление урока'),
        ('chat_message', 'Сообщение в чате'),
        ('support_chat', 'Обращение в поддержку'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name='Тип действия')
    action_time = models.DateTimeField(auto_now_add=True, verbose_name='Время действия')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    object_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='Тип объекта')
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID объекта')
    object_repr = models.CharField(max_length=200, null=True, blank=True, verbose_name='Представление объекта')
    details = models.JSONField(default=dict, blank=True, verbose_name='Детали')
    
    class Meta:
        verbose_name = 'Лог активности'
        verbose_name_plural = 'Логи активности'
        ordering = ['-action_time']
        indexes = [
            models.Index(fields=['user', 'action_time']),
            models.Index(fields=['action_type', 'action_time']),
            models.Index(fields=['action_time']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.action_time}"
    
    @property
    def action_display(self):
        return self.get_action_type_display()


class SystemLog(models.Model):
    """Системные логи"""
    LOG_LEVELS = [
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ]
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS, verbose_name='Уровень')
    message = models.TextField(verbose_name='Сообщение')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    module = models.CharField(max_length=100, null=True, blank=True, verbose_name='Модуль')
    function = models.CharField(max_length=100, null=True, blank=True, verbose_name='Функция')
    line_number = models.PositiveIntegerField(null=True, blank=True, verbose_name='Номер строки')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    request_id = models.CharField(max_length=50, null=True, blank=True, verbose_name='ID запроса')
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='Дополнительные данные')
    
    class Meta:
        verbose_name = 'Системный лог'
        verbose_name_plural = 'Системные логи'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['module', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.timestamp} - {self.message[:50]}"


class BackupLog(models.Model):
    """Логи бэкапов"""
    STATUS_CHOICES = [
        ('started', 'Начат'),
        ('completed', 'Завершен'),
        ('failed', 'Ошибка'),
        ('cancelled', 'Отменен'),
    ]
    
    backup_type = models.CharField(max_length=20, verbose_name='Тип бэкапа')  # full, incremental, etc.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Время начала')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Время завершения')
    file_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='Путь к файлу')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='Размер файла (байты)')
    tables_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Количество таблиц')
    records_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Количество записей')
    error_message = models.TextField(null=True, blank=True, verbose_name='Сообщение об ошибке')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Кто создал')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Лог бэкапа'
        verbose_name_plural = 'Логи бэкапов'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Бэкап {self.backup_type} - {self.status} - {self.started_at}"
    
    @property
    def duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        return None


class UserSession(models.Model):
    """Сессии пользователей"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    session_key = models.CharField(max_length=40, verbose_name='Ключ сессии')
    ip_address = models.GenericIPAddressField(verbose_name='IP адрес')
    user_agent = models.TextField(verbose_name='User Agent')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Время начала')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='Последняя активность')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    page_views = models.PositiveIntegerField(default=0, verbose_name='Просмотров страниц')
    
    class Meta:
        verbose_name = 'Сессия пользователя'
        verbose_name_plural = 'Сессии пользователей'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'last_activity']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active', 'last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.started_at}"
    
    @property
    def duration(self):
        return self.last_activity - self.started_at


class PopularContent(models.Model):
    """Популярный контент"""
    CONTENT_TYPES = [
        ('course', 'Курс'),
        ('lesson', 'Урок'),
        ('user', 'Пользователь'),
        ('language', 'Язык программирования'),
    ]
    
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, verbose_name='Тип контента')
    content_id = models.PositiveIntegerField(verbose_name='ID контента')
    title = models.CharField(max_length=200, verbose_name='Название')
    view_count = models.PositiveIntegerField(default=0, verbose_name='Количество просмотров')
    unique_views = models.PositiveIntegerField(default=0, verbose_name='Уникальные просмотры')
    enrollment_count = models.PositiveIntegerField(default=0, verbose_name='Количество записей')
    completion_count = models.PositiveIntegerField(default=0, verbose_name='Количество завершений')
    last_accessed = models.DateTimeField(auto_now=True, verbose_name='Последний доступ')
    popularity_score = models.FloatField(default=0.0, verbose_name='Рейтинг популярности')
    
    class Meta:
        verbose_name = 'Популярный контент'
        verbose_name_plural = 'Популярный контент'
        ordering = ['-popularity_score']
        unique_together = ['content_type', 'content_id']
        indexes = [
            models.Index(fields=['content_type', 'popularity_score']),
            models.Index(fields=['last_accessed']),
        ]
    
    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"
    
    def calculate_popularity_score(self):
        """Расчет рейтинга популярности"""
        # Веса для разных факторов
        view_weight = 1
        unique_view_weight = 2
        enrollment_weight = 5
        completion_weight = 10
        
        # Бонус за свежесть (контент за последние 30 дней)
        from datetime import datetime, timedelta
        recent_bonus = 0
        if self.last_accessed > datetime.now() - timedelta(days=30):
            recent_bonus = 20
        
        self.popularity_score = (
            self.view_count * view_weight +
            self.unique_views * unique_view_weight +
            self.enrollment_count * enrollment_weight +
            self.completion_count * completion_weight +
            recent_bonus
        )
        self.save(update_fields=['popularity_score'])


class ErrorLog(models.Model):
    """Логи ошибок приложения"""
    ERROR_TYPES = [
        ('404', 'Not Found'),
        ('500', 'Internal Server Error'),
        ('403', 'Forbidden'),
        ('400', 'Bad Request'),
        ('javascript', 'JavaScript Error'),
        ('python', 'Python Error'),
        ('database', 'Database Error'),
        ('other', 'Other'),
    ]
    
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES, verbose_name='Тип ошибки')
    message = models.TextField(verbose_name='Сообщение об ошибке')
    stack_trace = models.TextField(null=True, blank=True, verbose_name='Stack Trace')
    url = models.URLField(max_length=500, null=True, blank=True, verbose_name='URL')
    method = models.CharField(max_length=10, null=True, blank=True, verbose_name='HTTP метод')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP адрес')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    resolved = models.BooleanField(default=False, verbose_name='Решена')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Время решения')
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='resolved_errors', verbose_name='Кто решил')
    
    class Meta:
        verbose_name = 'Лог ошибок'
        verbose_name_plural = 'Логи ошибок'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['error_type', 'timestamp']),
            models.Index(fields=['resolved', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.error_type} - {self.timestamp} - {self.message[:50]}"
