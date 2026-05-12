from django.contrib.auth.models import AbstractUser
from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice
from urllib.parse import quote
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
        ('admin', 'Администратор'),
    ]
    
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def avatar_url(self):
        name = (self.get_full_name() or self.username or self.email or "User").strip()
        fallback = f"https://ui-avatars.com/api/?background=0D6EFD&color=fff&name={quote(name)}&size=128"

        if not self.avatar or not getattr(self.avatar, "name", None):
            return fallback

        try:
            if not self.avatar.storage.exists(self.avatar.name):
                return fallback
        except Exception:
            pass

        try:
            return self.avatar.url
        except Exception:
            return fallback

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name='Биография')
    specialization = models.CharField(max_length=100, blank=True, null=True, verbose_name='Специализация')
    learning_progress = models.JSONField(default=dict, blank=True, verbose_name='Прогресс обучения')
    achievements = models.JSONField(default=list, blank=True, verbose_name='Достижения')
    preferences = models.JSONField(default=dict, blank=True, verbose_name='Настройки')
    two_factor_enabled = models.BooleanField(default=False, verbose_name='Двухфакторная аутентификация')
    backup_codes = models.JSONField(default=list, blank=True, verbose_name='Резервные коды')
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    def get_totp_device(self):
        """Получить или создать TOTP устройство"""
        device, created = TOTPDevice.objects.get_or_create(
            user=self.user,
            name='Progage 2FA',
            confirmed=True
        )
        return device
    
    def verify_backup_code(self, code):
        """Проверить резервный код"""
        if not code or not self.backup_codes:
            return False
        
        # Ищем код в списке резервных кодов
        for i, backup_code in enumerate(self.backup_codes):
            if backup_code == code:
                # Удаляем использованный код
                self.backup_codes.pop(i)
                self.save()
                return True
        
        return False
    
    def generate_backup_codes(self):
        """Сгенерировать новые резервные коды"""
        import secrets
        import string
        
        # Генерируем 10 кодов по 8 символов
        codes = []
        for _ in range(10):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        
        self.backup_codes = codes
        self.save()
        return codes


class TeacherRating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Ужасно'),
        (2, '2 - Плохо'),
        (3, '3 - Нормально'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_ratings', verbose_name='Студент')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received', verbose_name='Преподаватель')
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name='Оценка')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Оценка преподавателя'
        verbose_name_plural = 'Оценки преподавателей'
        unique_together = ('student', 'teacher')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Оценка {self.student.username} -> {self.teacher.username}: {self.rating}"
    
    def generate_backup_codes(self):
        """Сгенерировать резервные коды"""
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = codes
        self.save()
        return codes
    
    def verify_backup_code(self, code):
        """Проверить резервный код"""
        if code.upper() in self.backup_codes:
            self.backup_codes.remove(code.upper())
            self.save()
            return True
        return False


class Notification(models.Model):
    TYPE_CHOICES = [
        ('new_chat', 'Новый чат'),
        ('new_chat_message', 'Новое сообщение в чате'),
        ('course_enrollment', 'Запись на курс'),
        ('course_review', 'Отзыв на курс'),
        ('new_lesson', 'Новый урок'),
        ('system', 'Системное уведомление'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Опциональные поля для ссылок
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    chat_room_id = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    @classmethod
    def create_notification(cls, user, type, title, message):
        """Создать уведомление"""
        return cls.objects.create(
            user=user,
            type=type,
            title=title,
            message=message
        )

class UserNotifications(models.Model):
    """Настройки уведомлений пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    support_messages = models.BooleanField(default=True, verbose_name='Уведомления из поддержки')
    new_lessons = models.BooleanField(default=True, verbose_name='Новые уроки')
    
    class Meta:
        verbose_name = 'Настройки уведомлений'
        verbose_name_plural = 'Настройки уведомлений'
    
    def __str__(self):
        return f"Настройки уведомлений: {self.user.username}"

class UserPrivacy(models.Model):
    """Настройки приватности пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_settings')
    public_profile = models.BooleanField(default=False, verbose_name='Публичный профиль')
    show_email = models.BooleanField(default=False, verbose_name='Показывать email')
    show_progress = models.BooleanField(default=True, verbose_name='Показывать прогресс обучения')
    
    class Meta:
        verbose_name = 'Настройки приватности'
        verbose_name_plural = 'Настройки приватности'
    
    def __str__(self):
        return f"Настройки приватности: {self.user.username}"
