from django.contrib.auth.models import AbstractUser
from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice
from urllib.parse import quote

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    learning_progress = models.JSONField(default=dict)
    achievements = models.JSONField(default=list)
    preferences = models.JSONField(default=dict)
    two_factor_enabled = models.BooleanField(default=False, verbose_name='Двухфакторная аутентификация')
    backup_codes = models.JSONField(default=list, blank=True, verbose_name='Резервные коды')
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def get_totp_device(self):
        """Получить или создать TOTP устройство"""
        device, created = TOTPDevice.objects.get_or_create(
            user=self.user,
            name='Progage 2FA',
            confirmed=True
        )
        return device
    
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
