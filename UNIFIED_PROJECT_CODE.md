# UNIFIED PROJECT CODE - ACCOUNTS MODULE

## accounts/__init__.py
```python
```

## accounts/admin.py
```python
from django.contrib import admin

# Register your models here.
```

## accounts/apps.py
```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
```

## accounts/context_processors.py
```python
from django.conf import settings

def recaptcha_enabled(request):
    """Adds reCAPTCHA enabled status to context"""
    return {
        'RECAPTCHA_ENABLED': (
            hasattr(settings, 'RECAPTCHA_PUBLIC_KEY') and 
            settings.RECAPTCHA_PUBLIC_KEY and 
            'test' not in settings.RECAPTCHA_PUBLIC_KEY
        )
    }
```

## accounts/email_utils.py
```python
from django.core.mail import get_connection, EmailMessage
from django.conf import settings

_connection = None

def get_smtp_connection():
    global _connection
    if _connection is None:
        _connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            fail_silently=False,
        )
        _connection.open()  # open once
    return _connection


def send_email(subject, body, to):
    connection = get_smtp_connection()

    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to],
        connection=connection,
    )

    email.send()
```

## accounts/forms.py
```python
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.conf import settings
from .models import User, Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=30, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    avatar = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reCAPTCHA completely disabled

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'avatar')

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'avatar', 'bio', 'phone')

class ProfileUpdateForm(forms.ModelForm):
    two_factor_enabled = forms.BooleanField(required=False, label='Enable two-factor authentication')
    
    class Meta:
        model = Profile
        fields = ('preferences', 'two_factor_enabled')

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Username or Email'
        self.fields['password'].label = 'Password'
        # reCAPTCHA removed

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email'}))

class TwoFactorForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autofocus': True,
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        }),
        label='Code from app',
        help_text='Enter 6-digit code from Google Authenticator'
    )
    
    backup_code = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ABCDEF12',
            'autocomplete': 'off'
        }),
        label='Backup code',
        help_text='If you don\'t have access to the app, use a backup code'
    )

class TwoFactorSetupForm(forms.Form):
    pass
```

## accounts/middleware.py
```python
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time

class BruteForceProtectionMiddleware(MiddlewareMixin):
    """Brute-force protection with rate limiting"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Apply only to login and password reset forms
        if request.path in ['/accounts/login/', '/accounts/password-reset/']:
            client_ip = self.get_client_ip(request)
            username = request.POST.get('username', '') if request.method == 'POST' else ''
            
            if self.is_blocked(client_ip, username):
                return HttpResponse(
                    "Too many attempts. Try again in 5 minutes.",
                    status=429
                )
            
            if request.method == 'POST':
                self.record_attempt(client_ip, username)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_blocked(self, ip, username=''):
        # Check block by IP and by username+IP
        ip_key = f'login_attempts_ip_{ip}'
        user_key = f'login_attempts_user_{username}_{ip}' if username else None
        
        ip_attempts = cache.get(ip_key, 0)
        user_attempts = cache.get(user_key, 0) if user_key else 0
        
        # Block if more than 5 attempts in 5 minutes
        return ip_attempts >= 5 or user_attempts >= 3
    
    def record_attempt(self, ip, username):
        # Record attempt with TTL 5 minutes
        ip_key = f'login_attempts_ip_{ip}'
        user_key = f'login_attempts_user_{username}_{ip}' if username else None
        
        # Safe increment with initialization
        if cache.get(ip_key) is None:
            cache.set(ip_key, 1, 300)
        else:
            cache.incr(ip_key)
        
        if user_key:
            if cache.get(user_key) is None:
                cache.set(user_key, 1, 300)
            else:
                cache.incr(user_key)
```

## accounts/models.py
```python
from django.contrib.auth.models import AbstractUser
from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice
from urllib.parse import quote

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
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
    two_factor_enabled = models.BooleanField(default=False, verbose_name='Two-factor authentication')
    backup_codes = models.JSONField(default=list, blank=True, verbose_name='Backup codes')
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def get_totp_device(self):
        """Get or create TOTP device"""
        device, created = TOTPDevice.objects.get_or_create(
            user=self.user,
            name='Progage 2FA',
            confirmed=True
        )
        return device
    
    def generate_backup_codes(self):
        """Generate backup codes"""
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.backup_codes = codes
        self.save()
        return codes
    
    def verify_backup_code(self, code):
        """Verify backup code"""
        if code.upper() in self.backup_codes:
            self.backup_codes.remove(code.upper())
            self.save()
            return True
        return False
```

## accounts/tests.py
```python
from django.test import TestCase

# Create your tests here.
```

## accounts/urls.py
```python
from django.urls import path
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('notifications/', views.notifications, name='notifications'),
    # Password reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html', success_url='/accounts/reset/done/'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    # Two-factor authentication URLs
    path('2fa/', views.two_factor_verify, name='two_factor_verify'),
    path('2fa/setup/', views.two_factor_setup, name='two_factor_setup'),
]
```

## accounts/views.py
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.core.cache import cache
from django.http import HttpResponse
from django_otp import devices_for_user
from .forms import (
    UserRegistrationForm, UserUpdateForm, ProfileUpdateForm,
    CustomAuthenticationForm, CustomPasswordResetForm, TwoFactorForm, TwoFactorSetupForm
)
from .models import User, Profile
from courses.models import Course, CourseEnrollment

UserModel = get_user_model()

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Check rate limiting before processing form
        client_ip = get_client_ip(request)
        username = request.POST.get('username', '')
        
        if is_rate_limited(client_ip, username):
            return HttpResponse(
                "Too many attempts. Try again in 5 minutes.",
                status=429
            )
        
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # In project USERNAME_FIELD = 'email', so authenticate expects email in username parameter.
            user = authenticate(username=username, password=password)

            # Support login by username: if entered not email, try to find user by username
            # and authorize by their email.
            if user is None and username and '@' not in username:
                try:
                    u = UserModel.objects.get(username__iexact=username)
                    user = authenticate(username=u.email, password=password)
                except UserModel.DoesNotExist:
                    user = None
                    
            if user is not None:
                # Check if 2FA is enabled
                try:
                    profile = user.profile
                    if profile.two_factor_enabled:
                        # Save user in session for 2FA verification
                        request.session['2fa_user_id'] = user.id
                        return redirect('accounts:two_factor_verify')
                except Profile.DoesNotExist:
                    pass
                
                # Reset attempt counter on successful login
                reset_login_attempts(client_ip, username)
                login(request, user)
                messages.info(request, f'You are logged in as {username}')
                return redirect('home')
            else:
                # Record failed attempt
                record_failed_attempt(client_ip, username)
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'accounts/login.html', {'form': form})
    form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def password_reset_request(request):
    """Password reset request"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='accounts/password_reset_email.html',
                subject_template_name='accounts/password_reset_subject.txt',
            )
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('accounts:password_reset_done')
    else:
        form = CustomPasswordResetForm()
    return render(request, 'accounts/password_reset.html', {'form': form})

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_rate_limited(ip, username=''):
    """Check if attempt limit is exceeded"""
    ip_key = f'login_attempts_ip_{ip}'
    user_key = f'login_attempts_user_{username}_{ip}' if username else None
    
    ip_attempts = cache.get(ip_key, 0)
    user_attempts = cache.get(user_key, 0) if user_key else 0
    
    return ip_attempts >= 5 or user_attempts >= 3

def record_failed_attempt(ip, username=''):
    """Record failed attempt"""
    ip_key = f'login_attempts_ip_{ip}'
    user_key = f'login_attempts_user_{username}_{ip}' if username else None
    
    # Safe increment with initialization
    if cache.get(ip_key) is None:
        cache.set(ip_key, 1, 300)
    else:
        cache.incr(ip_key)
    
    if user_key:
        if cache.get(user_key) is None:
            cache.set(user_key, 1, 300)
        else:
            cache.incr(user_key)

def reset_login_attempts(ip, username=''):
    """Reset attempt counter on successful login"""
    ip_key = f'login_attempts_ip_{ip}'
    user_key = f'login_attempts_user_{username}_{ip}' if username else None
    
    cache.delete(ip_key)
    if user_key:
        cache.delete(user_key)


@login_required
def notifications(request):
    # Project has notifications.html template, but no notification model/logic yet.
    # Return empty list to make page and navigation work.
    return render(request, 'accounts/notifications.html', {'notifications': []})

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            
            # First save profile_form
            profile_form.save()
            
            # Handle 2FA separately
            two_factor_enabled = request.POST.get('two_factor_enabled') == 'on'
            
            # Debug information
            print(f"DEBUG: two_factor_enabled = {two_factor_enabled}")
            print(f"DEBUG: POST data = {request.POST}")
            print(f"DEBUG: profile.two_factor_enabled (before) = {profile.two_factor_enabled}")
            
            if two_factor_enabled != profile.two_factor_enabled:
                if two_factor_enabled:
                    # Ensure TOTP device is created
                    device = profile.get_totp_device()
                    print(f"DEBUG: TOTP device created = {device}")
                    
                    # Enable 2FA - generate backup codes
                    backup_codes = profile.generate_backup_codes()
                    print(f"DEBUG: Backup codes generated = {backup_codes}")
                    
                    # Force set values
                    profile.two_factor_enabled = True
                    profile.backup_codes = backup_codes
                    profile.save()
                    
                    messages.success(request, 'Two-factor authentication enabled. Backup codes generated!')
                    print(f"DEBUG: profile.two_factor_enabled (after) = {profile.two_factor_enabled}")
                else:
                    # Disable 2FA - clear backup codes
                    profile.two_factor_enabled = False
                    profile.backup_codes = []
                    profile.save()
                    
                    messages.info(request, 'Two-factor authentication disabled.')
                    print(f"DEBUG: 2FA disabled")
            else:
                # If status didn't change, just save current value
                profile.two_factor_enabled = two_factor_enabled
                profile.save()
                print(f"DEBUG: No change in 2FA status")
            
            if two_factor_enabled and not profile.backup_codes:
                messages.success(request, 'Your profile has been updated! Two-factor authentication enabled.')
            elif not two_factor_enabled:
                messages.success(request, 'Your profile has been updated! Two-factor authentication disabled.')
            else:
                messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/profile.html', context)

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('home')

@login_required
def dashboard(request):
    enrollments = CourseEnrollment.objects.filter(user=request.user).select_related('course')
    context = {
        'enrollments': enrollments,
        'completed_count': enrollments.filter(progress=100).count(),
        'in_progress_count': enrollments.filter(progress__lt=100).count(),
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        messages.error(request, 'Access only for teachers')
        return redirect('home')
    
    courses = Course.objects.filter(instructor=request.user)
    context = {
        'courses': courses,
        'total_students': sum(course.enrollment_count for course in courses),
    }
    return render(request, 'accounts/teacher_dashboard.html', context)

def two_factor_verify(request):
    """Two-factor code verification"""
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return redirect('accounts:login')
    
    user = get_object_or_404(UserModel, id=user_id)
    profile = user.profile
    
    if request.method == 'POST':
        form = TwoFactorForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('code')
            backup_code = form.cleaned_data.get('backup_code')
            
            # Check TOTP code
            if code:
                device = profile.get_totp_device()
                if device.verify_token(code):
                    # Successful 2FA verification
                    del request.session['2fa_user_id']
                    login(request, user)
                    messages.success(request, 'You have successfully logged in!')
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid code from app')
            
            # Check backup code
            elif backup_code:
                if profile.verify_backup_code(backup_code):
                    # Successful backup code verification
                    del request.session['2fa_user_id']
                    login(request, user)
                    messages.success(request, 'You have successfully logged in using backup code!')
                    messages.warning(request, 'It is recommended to generate new backup codes in your profile.')
                    return redirect('home')
                else:
                    messages.error(request, 'Invalid backup code')
            else:
                messages.error(request, 'Enter code from app or backup code')
    else:
        form = TwoFactorForm()
    
    return render(request, 'accounts/two_factor_verify.html', {
        'form': form,
        'user': user
    })

@login_required
def two_factor_setup(request):
    """Two-factor authentication setup"""
    profile = request.user.profile
    
    if request.method == 'POST':
        action = request.POST.get('action')
        print(f"DEBUG: two_factor_setup POST action = {action}")
        print(f"DEBUG: POST data = {request.POST}")
        print(f"DEBUG: profile.two_factor_enabled (before) = {profile.two_factor_enabled}")
        
        if action == 'enable':
            # Ensure TOTP device is created before enabling 2FA
            device = profile.get_totp_device()
            print(f"DEBUG: TOTP device created/verified: {device}")
            
            # Enable 2FA
            profile.two_factor_enabled = True
            profile.backup_codes = profile.generate_backup_codes()
            profile.save()
            
            print(f"DEBUG: 2FA enabled, backup_codes: {profile.backup_codes}")
            print(f"DEBUG: profile.two_factor_enabled = {profile.two_factor_enabled}")
            
            messages.success(request, 'Two-factor authentication enabled. Save backup codes safely!')
            
        elif action == 'disable':
            # Turn off 2FA
            print(f"DEBUG: DISABLING 2FA - was {profile.two_factor_enabled}")
            profile.two_factor_enabled = False
            profile.backup_codes = []
            profile.save()
            print(f"DEBUG: 2FA disabled, now = {profile.two_factor_enabled}")
            messages.success(request, 'Two-factor authentication disabled.')
            
        elif action == 'regenerate_codes':
            # Regenerate backup codes
            profile.backup_codes = profile.generate_backup_codes()
            profile.save()
            messages.success(request, 'Backup codes updated.')
            
        return redirect('accounts:profile')
    
    # Get QR code for setup
    device = profile.get_totp_device()
    qr_code_url = device.config_url
    
    return render(request, 'accounts/two_factor_setup.html', {
        'device': device,
        'qr_code_url': qr_code_url,
        'backup_codes': profile.backup_codes if profile.backup_codes else None
    })
```

---

# ADMINPANEL MODULE

## adminpanel/__init__.py
```python
```

## adminpanel/admin.py
```python
from django.contrib import admin

# Register your models here.
```

## adminpanel/apps.py
```python
from django.apps import AppConfig


class AdminpanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adminpanel'
```

## adminpanel/backup_utils.py
```python
import os
import json
import zipfile
import shutil
from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.http import HttpResponse
from django.contrib.auth.models import User
from accounts.models import User as UserModel
from courses.models import Course, Lesson, CourseEnrollment, CourseLike, CourseReview
from chat.models import Message, SupportChat
from adminpanel.models import ActivityLog, SystemLog, ErrorLog, UserSession, BackupLog, PopularContent
from .models import BackupLog as AdminBackupLog


class SystemBackup:
    """Class for creating full system backups"""
    
    def __init__(self):
        # Create backup directory in project root
        self.backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create backup directory"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print(f"Backup directory created: {self.backup_dir}")
    
    def get_backup_info(self):
        """Get backup directory information"""
        return {
            'backup_dir': self.backup_dir,
            'exists': os.path.exists(self.backup_dir),
            'writable': os.access(self.backup_dir, os.W_OK) if os.path.exists(self.backup_dir) else False
        }
    
    def create_full_backup(self, user=None):
        """Create full system backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"full_backup_{timestamp}.zip"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        print(f"Starting backup: {backup_filename}")
        print(f"Save path: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # 1. Database backup
                print("Creating database backup...")
                self._backup_database(backup_zip)
                
                # 2. Media files backup
                print("Creating media files backup...")
                self._backup_media_files(backup_zip)
                
                # 3. Configuration files backup
                print("Creating configuration backup...")
                self._backup_config_files(backup_zip)
                
                # 4. Logs backup
                print("Creating logs backup...")
                self._backup_logs(backup_zip)
                
                # 5. Backup metadata creation
                print("Creating metadata...")
                self._create_backup_metadata(backup_zip, timestamp)
            
            # Log backup creation
            self._log_backup_creation(backup_filename, backup_path, user, True)
            
            file_size = os.path.getsize(backup_path)
            print(f"Backup successfully created: {backup_filename} ({file_size} bytes)")
            
            return {
                'success': True,
                'filename': backup_filename,
                'path': backup_path,
                'size': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2),
                'timestamp': timestamp,
                'backup_dir': self.backup_dir
            }
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            # Log error
            self._log_backup_creation(backup_filename, backup_path, user, False, str(e))
            raise
    
    def _backup_database(self, backup_zip):
        """Database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create SQL dump via Django management command
        sql_filename = f"database_dump_{timestamp}.sql"
        sql_path = os.path.join(self.backup_dir, sql_filename)
        
        try:
            # Use Django command to create dump
            with open(sql_path, 'w', encoding='utf-8') as f:
                call_command('dumpdata', '--natural-foreign', '--natural-primary', 
                           '--indent=2', stdout=f)
            
            backup_zip.write(sql_path, f"database/{sql_filename}")
            os.remove(sql_path)  # Remove temporary file
            print(f"Database saved: {sql_filename}")
            
        except Exception as e:
            print(f"Error creating SQL dump: {e}")
            # Alternative method via direct SQL
            self._backup_database_direct(backup_zip)
    
    def _backup_database_direct(self, backup_zip):
        """Direct database backup via SQL"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    print(f"Backing up table: {table_name}")
                    
                    cursor.execute(f"SELECT * FROM `{table_name}`")
                    rows = cursor.fetchall()
                    
                    # Get column names
                    cursor.execute(f"DESCRIBE `{table_name}`")
                    columns = [col[0] for col in cursor.fetchall()]
                    
                    # Create JSON for table
                    table_data = {
                        'table': table_name,
                        'columns': columns,
                        'rows': rows,
                        'row_count': len(rows)
                    }
                    
                    table_filename = f"database/table_{table_name}_{timestamp}.json"
                    backup_zip.writestr(table_filename, json.dumps(table_data, 
                                     ensure_ascii=False, indent=2, default=str))
        
        except Exception as e:
            print(f"Error in direct DB backup: {e}")
            raise
    
    def _backup_media_files(self, backup_zip):
        """Media files backup"""
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        
        if media_root and os.path.exists(media_root):
            print(f"Backing up media files from: {media_root}")
            
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, media_root)
                    backup_zip.write(file_path, f"media/{arcname}")
            
            print(f"Media files saved to archive")
        else:
            print("Media directory not found")
    
    def _backup_config_files(self, backup_zip):
        """Configuration files backup"""
        config_files = [
            'progage/settings.py',
            'progage/urls.py',
            'requirements.txt',
            'manage.py',
            '.env',
            'README.md'
        ]
        
        print("Backing up configuration files:")
        
        for config_file in config_files:
            if os.path.exists(config_file):
                backup_zip.write(config_file, f"config/{config_file}")
                print(f"  - {config_file}")
            else:
                print(f"  - {config_file} (not found)")
    
    def _backup_logs(self, backup_zip):
        """Logs backup"""
        log_files = [
            'django.log',
            'debug.log', 
            'error.log',
            'access.log'
        ]
        
        print("Backing up log files:")
        
        for log_file in log_files:
            if os.path.exists(log_file):
                backup_zip.write(log_file, f"logs/{log_file}")
                print(f"  - {log_file}")
            else:
                print(f"  - {log_file} (not found)")
    
    def _create_backup_metadata(self, backup_zip, timestamp):
        """Create backup metadata"""
        metadata = {
            'backup_type': 'full_system_backup',
            'timestamp': timestamp,
            'started_at': datetime.now().isoformat(),
            'django_version': getattr(settings, 'VERSION', 'unknown'),
            'python_version': os.sys.version,
            'backup_dir': self.backup_dir,
            'base_dir': settings.BASE_DIR,
            'database_settings': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
            },
            'media_root': getattr(settings, 'MEDIA_ROOT', None),
            'statistics': self._get_system_statistics()
        }
        
        backup_zip.writestr('metadata.json', json.dumps(metadata, 
                             ensure_ascii=False, indent=2, default=str))
        print("Backup metadata created")
    
    def _get_system_statistics(self):
        """Get system statistics"""
        try:
            stats = {
                'users': UserModel.objects.count(),
                'courses': Course.objects.count(),
                'lessons': Lesson.objects.count(),
                'enrollments': CourseEnrollment.objects.count(),
                'likes': CourseLike.objects.count(),
                'reviews': CourseReview.objects.count(),
                'messages': Message.objects.count(),
                'support_chats': SupportChat.objects.count(),
                'activity_logs': ActivityLog.objects.count(),
                'system_logs': SystemLog.objects.count(),
                'error_logs': ErrorLog.objects.count(),
                'user_sessions': UserSession.objects.count(),
                'backup_logs': AdminBackupLog.objects.count(),
            }
            print(f"System statistics collected: {stats}")
            return stats
        except Exception as e:
            print(f"Error collecting statistics: {e}")
            return {'error': str(e)}
    
    def _log_backup_creation(self, filename, path, user, success, error=None):
        """Log backup creation"""
        try:
            status = 'success' if success else 'failed'
            file_size = os.path.getsize(path) if success and os.path.exists(path) else 0
            
            AdminBackupLog.objects.create(
                backup_type='full_system',
                filename=filename,
                file_path=path,
                file_size=file_size,
                status=status,
                created_by=user,
                details={
                    'error': error,
                    'timestamp': datetime.now().isoformat(),
                    'backup_dir': self.backup_dir
                }
            )
            
            # Also log to system log
            from .middleware import ActivityLogger
            ActivityLogger.log_system_event(
                level='INFO' if success else 'ERROR',
                message=f"[BACKUP] {'Successfully created' if success else 'Failed to create'} backup: {filename}",
                module='backup_system',
                function='create_full_backup',
                user=user,
                details={
                    'filename': filename,
                    'path': path,
                    'status': status,
                    'file_size': file_size,
                    'backup_dir': self.backup_dir,
                    'error': error
                }
            )
            
        except Exception as e:
            print(f"Error logging backup creation: {e}")
    
    def list_backups(self):
        """Get list of all backups"""
        backups = []
        
        if os.path.exists(self.backup_dir):
            print(f"Searching backups in directory: {self.backup_dir}")
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    
                    backup_info = {
                        'filename': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    }
                    backups.append(backup_info)
                    print(f"Found backup: {filename} ({backup_info['size_mb']} MB)")
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def delete_backup(self, filename, user=None):
        """Delete backup"""
        try:
            file_path = os.path.join(self.backup_dir, filename)
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                
                print(f"Backup deleted: {filename}")
                
                # Log deletion
                AdminBackupLog.objects.create(
                    backup_type='delete',
                    filename=filename,
                    file_path=file_path,
                    file_size=file_size,
                    status='success',
                    created_by=user,
                    details={
                        'operation': 'delete',
                        'timestamp': datetime.now().isoformat(),
                        'backup_dir': self.backup_dir
                    }
                )
                
                return True
            else:
                print(f"Backup file not found: {file_path}")
                return False
                
        except Exception as e:
            print(f"Error deleting backup: {e}")
            
            # Log error
            AdminBackupLog.objects.create(
                backup_type='delete',
                filename=filename,
                file_path=os.path.join(self.backup_dir, filename),
                status='failed',
                created_by=user,
                details={
                    'operation': 'delete',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'backup_dir': self.backup_dir
                }
            )
            return False
    
    def get_backup_path(self, filename):
        """Get full path to backup file"""
        return os.path.join(self.backup_dir, filename)
    
    def backup_exists(self, filename):
        """Check if backup exists"""
        file_path = self.get_backup_path(filename)
        return os.path.exists(file_path) and filename.endswith('.zip')
```

## adminpanel/decorators.py
```python
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in.')
            return redirect('accounts:login')
        if request.user.role != 'admin':
            messages.error(request, 'You do not have access to admin panel.')
            return redirect('courses:course_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
```

## adminpanel/forms.py
```python
from django import forms
from django.contrib.auth import get_user_model
from courses.models import Course

User = get_user_model()


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave empty to not change password'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'date_of_birth', 'avatar', 'bio', 'is_active', 'role'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Login',
            'email': 'Email',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'phone': 'Phone',
            'date_of_birth': 'Date of Birth',
            'avatar': 'Avatar',
            'bio': 'About',
            'is_active': 'Active User',
            'role': 'Role',
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'instructor', 'category', 'level', 'price',
            'thumbnail', 'is_published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Course Title',
            'description': 'Description',
            'instructor': 'Instructor',
            'category': 'Category',
            'level': 'Difficulty Level',
            'price': 'Price (RUB)',
            'thumbnail': 'Preview',
            'is_published': 'Published',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit instructor selection to teachers only
        self.fields['instructor'].queryset = User.objects.filter(role='teacher')
```

## adminpanel/middleware.py
```python
import logging
import json
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.http import JsonResponse
from .models import ActivityLog, UserSession, ErrorLog, SystemLog
import uuid

logger = logging.getLogger(__name__)

class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.request_id = str(uuid.uuid4())
        request.start_time = timezone.now()
        
        # Log all requests
        self._log_request(request)
        
        return None
    
    def process_response(self, request, response):
        # Log responses
        self._log_response(request, response)
        
        # Log HTTP errors
        if hasattr(response, 'status_code') and response.status_code >= 400:
            self._log_http_error(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        # Log exceptions
        self._log_exception(request, exception)
        return None
    
    def _log_request(self, request):
        """Log incoming requests"""
        try:
            # Determine request type
            request_type = 'HTTP'
            if request.path.startswith('/api/'):
                request_type = 'API'
            elif request.path.startswith('/admin/'):
                request_type = 'ADMIN'
            elif 'application/json' in request.content_type:
                request_type = 'JSON_API'
            
            # Log to SystemLog
            SystemLog.objects.create(
                level='INFO',
                message=f"[{request_type}] {request.method} {request.path}",
                module='middleware',
                function='process_request',
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request),
                extra_data={
                    'request_id': request.request_id,
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'content_type': request.content_type,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'request_type': request_type,
                    'headers': dict(request.headers),
                }
            )
            
            # Additional logging for API requests
            if request_type == 'API' or request_type == 'JSON_API':
                try:
                    body = request.body.decode('utf-8')
                    if body and len(body) < 10000:  # Size limit
                        SystemLog.objects.create(
                            level='DEBUG',
                            message=f"[API_BODY] {request.method} {request.path}",
                            module='middleware',
                            function='log_api_body',
                            user=request.user if not isinstance(request.user, AnonymousUser) else None,
                            ip_address=self._get_client_ip(request),
                            extra_data={
                                'request_id': request.request_id,
                                'method': request.method,
                                'path': request.path,
                                'body': body,
                                'content_type': request.content_type,
                            }
                        )
                except Exception as e:
                    logger.error(f"Error logging API body: {e}")
            
        except Exception as e:
            logger.error(f"Error in _log_request: {e}")
    
    def _log_response(self, request, response):
        """Log responses"""
        try:
            duration = (timezone.now() - request.start_time).total_seconds()
            
            # Determine response type
            response_type = 'HTTP'
            if isinstance(response, JsonResponse):
                response_type = 'JSON'
            elif hasattr(response, 'Content-Type') and 'application/json' in response.get('Content-Type', ''):
                response_type = 'JSON'
            
            # Log slow requests
            if duration > 2.0:  # Requests longer than 2 seconds
                SystemLog.objects.create(
                    level='WARNING',
                    message=f"[SLOW_REQUEST] {request.method} {request.path} - {duration:.2f}s",
                    module='middleware',
                    function='process_response',
                    user=request.user if not isinstance(request.user, AnonymousUser) else None,
                    ip_address=self._get_client_ip(request),
                    extra_data={
                        'request_id': request.request_id,
                        'method': request.method,
                        'path': request.path,
                        'duration': duration,
                        'status_code': getattr(response, 'status_code', 0),
                        'response_type': response_type,
                    }
                )
            
            # Log all responses
            SystemLog.objects.create(
                level='INFO',
                message=f"[{response_type}] {request.method} {request.path} -> {getattr(response, 'status_code', 0)}",
                module='middleware',
                function='process_response',
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request),
                extra_data={
                    'request_id': request.request_id,
                    'method': request.method,
                    'path': request.path,
                    'status_code': getattr(response, 'status_code', 0),
                    'duration': duration,
                    'response_type': response_type,
                    'content_length': len(getattr(response, 'content', b'')),
                }
            )
            
        except Exception as e:
            logger.error(f"Error in _log_response: {e}")
    
    def _log_http_error(self, request, response):
        """Log HTTP errors"""
        try:
            ErrorLog.objects.create(
                error_type=str(response.status_code),
                message=f"HTTP {response.status_code}: {request.method} {request.path}",
                url=request.get_full_path(),
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request)
            )
        except Exception as e:
            logger.error(f"Error in _log_http_error: {e}")
    
    def _log_exception(self, request, exception):
        """Log exceptions"""
        try:
            ErrorLog.objects.create(
                error_type='EXCEPTION',
                message=str(exception),
                stack_trace=traceback.format_exc(),
                url=request.get_full_path(),
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request)
            )
        except Exception as e:
            logger.error(f"Error in _log_exception: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        """Log unhandled exceptions"""
        try:
            ErrorLog.objects.create(
                error_type='UNHANDLED_EXCEPTION',
                message=str(exception),
                stack_trace=traceback.format_exc(),
                url=request.get_full_path(),
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request)
            )
        except Exception as e:
            logger.error(f"Error in ExceptionLoggingMiddleware: {e}")
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ActivityLogger:
    """Class for convenient action logging"""
    
    @staticmethod
    def log_action(user, action_type, object_type=None, object_id=None, object_repr=None, details=None, request=None):
        """Log user action"""
        try:
            ip_address = None
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
            
            ActivityLog.objects.create(
                user=user,
                action_type=action_type,
                object_type=object_type,
                object_id=object_id,
                object_repr=object_repr,
                details=details or {},
                ip_address=ip_address
            )
            
            # Additional logging to SystemLog
            SystemLog.objects.create(
                level='INFO',
                message=f"[ACTIVITY] {action_type}: {object_repr or 'N/A'}",
                module='activity_logger',
                function='log_action',
                user=user,
                ip_address=ip_address,
                extra_data={
                    'action_type': action_type,
                    'object_type': object_type,
                    'object_id': object_id,
                    'object_repr': object_repr,
                    'details': details or {},
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_action: {e}")
    
    @staticmethod
    def log_system_event(level, message, module='system', function='unknown', details=None, user=None):
        """Log system events"""
        try:
            SystemLog.objects.create(
                level=level,
                message=message,
                module=module,
                function=function,
                user=user,
                extra_data=details or {}
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_system_event: {e}")
    
    @staticmethod
    def log_api_call(user, method, endpoint, request_data=None, response_data=None, status_code=200, duration=0):
        """Log API calls"""
        try:
            ActivityLogger.log_system_event(
                level='INFO',
                message=f"[API_CALL] {method} {endpoint} -> {status_code} ({duration:.3f}s)",
                module='api_logger',
                function='log_api_call',
                user=user,
                extra_data={
                    'method': method,
                    'endpoint': endpoint,
                    'request_data': request_data,
                    'response_data': response_data,
                    'status_code': status_code,
                    'duration': duration,
                }
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_api_call: {e}")
    
    @staticmethod
    def log_terminal_command(user, command, working_directory=None, exit_code=None, output=None, error=None):
        """Log terminal commands"""
        try:
            level = 'ERROR' if exit_code and exit_code != 0 else 'INFO'
            message = f"[TERMINAL] {command}"
            if exit_code is not None:
                message += f" -> {exit_code}"
            
            ActivityLogger.log_system_event(
                level=level,
                message=message,
                module='terminal_logger',
                function='log_terminal_command',
                user=user,
                extra_data={
                    'command': command,
                    'working_directory': working_directory,
                    'exit_code': exit_code,
                    'output': output,
                    'error': error,
                }
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_terminal_command: {e}")
    
    @staticmethod
    def log_database_query(user, query_type, table, query=None, duration=0, rows_affected=None):
        """Log database queries"""
        try:
            level = 'WARNING' if duration > 1.0 else 'DEBUG'
            message = f"[DB_QUERY] {query_type} {table}"
            if duration > 0:
                message += f" ({duration:.3f}s)"
            if rows_affected is not None:
                message += f" - {rows_affected} rows"
            
            ActivityLogger.log_system_event(
                level=level,
                message=message,
                module='db_logger',
                function='log_database_query',
                user=user,
                extra_data={
                    'query_type': query_type,
                    'table': table,
                    'query': query,
                    'duration': duration,
                    'rows_affected': rows_affected,
                }
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_database_query: {e}")
```

## adminpanel/models.py
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from courses.models import Course, CourseEnrollment, Lesson
import json

User = get_user_model()


class ActivityLog(models.Model):
    """User activity logs"""
    ACTION_TYPES = [
        ('login', 'System Login'),
        ('logout', 'System Logout'),
        ('view_course', 'View Course'),
        ('enroll_course', 'Enroll in Course'),
        ('complete_lesson', 'Complete Lesson'),
        ('start_lesson', 'Start Lesson'),
        ('submit_assignment', 'Submit Assignment'),
        ('view_profile', 'View Profile'),
        ('update_profile', 'Update Profile'),
        ('create_course', 'Create Course'),
        ('update_course', 'Update Course'),
        ('delete_course', 'Delete Course'),
        ('create_lesson', 'Create Lesson'),
        ('update_lesson', 'Update Lesson'),
        ('delete_lesson', 'Delete Lesson'),
        ('chat_message', 'Chat Message'),
        ('support_chat', 'Support Chat'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='User')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name='Action Type')
    action_time = models.DateTimeField(auto_now_add=True, verbose_name='Action Time')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    object_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='Object Type')
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='Object ID')
    object_repr = models.CharField(max_length=200, null=True, blank=True, verbose_name='Object Representation')
    details = models.JSONField(default=dict, blank=True, verbose_name='Details')
    
    class Meta:
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
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
    """System logs"""
    LOG_LEVELS = [
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ]
    
    level = models.CharField(max_length=10, choices=LOG_LEVELS, verbose_name='Level')
    message = models.TextField(verbose_name='Message')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Timestamp')
    module = models.CharField(max_length=100, null=True, blank=True, verbose_name='Module')
    function = models.CharField(max_length=100, null=True, blank=True, verbose_name='Function')
    line_number = models.PositiveIntegerField(null=True, blank=True, verbose_name='Line Number')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='User')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    request_id = models.CharField(max_length=50, null=True, blank=True, verbose_name='Request ID')
    extra_data = models.JSONField(default=dict, blank=True, verbose_name='Extra Data')
    
    class Meta:
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['module', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.timestamp} - {self.message[:50]}"


class BackupLog(models.Model):
    """Backup logs"""
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    backup_type = models.CharField(max_length=20, verbose_name='Backup Type')  # full, incremental, etc.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Status')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Start Time')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completion Time')
    file_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='File Path')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='File Size (bytes)')
    tables_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Tables Count')
    records_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Records Count')
    error_message = models.TextField(null=True, blank=True, verbose_name='Error Message')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Created By')
    description = models.TextField(null=True, blank=True, verbose_name='Description')
    
    class Meta:
        verbose_name = 'Backup Log'
        verbose_name_plural = 'Backup Logs'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Backup {self.backup_type} - {self.status} - {self.started_at}"
    
    @property
    def duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        return None


class UserSession(models.Model):
    """User sessions"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='User')
    session_key = models.CharField(max_length=40, verbose_name='Session Key')
    ip_address = models.GenericIPAddressField(verbose_name='IP Address')
    user_agent = models.TextField(verbose_name='User Agent')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Start Time')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='Last Activity')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    page_views = models.PositiveIntegerField(default=0, verbose_name='Page Views')
    
    class Meta:
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
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
    """Popular content"""
    CONTENT_TYPES = [
        ('course', 'Course'),
        ('lesson', 'Lesson'),
        ('user', 'User'),
        ('language', 'Programming Language'),
    ]
    
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, verbose_name='Content Type')
    content_id = models.PositiveIntegerField(verbose_name='Content ID')
    title = models.CharField(max_length=200, verbose_name='Title')
    view_count = models.PositiveIntegerField(default=0, verbose_name='View Count')
    unique_views = models.PositiveIntegerField(default=0, verbose_name='Unique Views')
    enrollment_count = models.PositiveIntegerField(default=0, verbose_name='Enrollment Count')
    completion_count = models.PositiveIntegerField(default=0, verbose_name='Completion Count')
    last_accessed = models.DateTimeField(auto_now=True, verbose_name='Last Accessed')
    popularity_score = models.FloatField(default=0.0, verbose_name='Popularity Score')
    
    class Meta:
        verbose_name = 'Popular Content'
        verbose_name_plural = 'Popular Content'
        ordering = ['-popularity_score']
        unique_together = ['content_type', 'content_id']
        indexes = [
            models.Index(fields=['content_type', 'popularity_score']),
            models.Index(fields=['last_accessed']),
        ]
    
    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"
    
    def calculate_popularity_score(self):
        """Calculate popularity score"""
        # Weights for different factors
        view_weight = 1
        unique_view_weight = 2
        enrollment_weight = 5
        completion_weight = 10
        
        # Freshness bonus (content from last 30 days)
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
    """Application error logs"""
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
    
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES, verbose_name='Error Type')
    message = models.TextField(verbose_name='Error Message')
    stack_trace = models.TextField(null=True, blank=True, verbose_name='Stack Trace')
    url = models.URLField(max_length=500, null=True, blank=True, verbose_name='URL')
    method = models.CharField(max_length=10, null=True, blank=True, verbose_name='HTTP Method')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='User')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Address')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Timestamp')
    resolved = models.BooleanField(default=False, verbose_name='Resolved')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Resolution Time')
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='resolved_errors', verbose_name='Resolved By')
    
    class Meta:
        verbose_name = 'Error Log'
        verbose_name_plural = 'Error Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['error_type', 'timestamp']),
            models.Index(fields=['resolved', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.error_type} - {self.timestamp} - {self.message[:50]}"
```

## adminpanel/tests.py
```python
from django.test import TestCase

# Create your tests here.
```

## adminpanel/urls.py
```python
from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Logging
    path('logs/activity/', views.activity_logs, name='activity_logs'),
    path('logs/system/', views.system_logs, name='system_logs'),
    path('logs/errors/', views.error_logs, name='error_logs'),
    path('logs/errors/<int:error_id>/resolve/', views.resolve_error, name='resolve_error'),
    path('logs/sessions/', views.user_sessions, name='user_sessions'),
    path('logs/popular/', views.popular_content, name='popular_content'),
    
    # Backups
    path('backups/', views.backup_logs, name='backup_logs'),
    path('backups/create/', views.create_backup, name='create_backup'),
    path('backups/<str:filename>/download/', views.download_backup, name='download_backup'),
    path('backups/<str:filename>/delete/', views.delete_backup, name='delete_backup'),
    path('backups/<str:filename>/restore/', views.restore_backup, name='restore_backup'),
    
    # Statistics
    path('statistics/', views.statistics, name='statistics'),
    
    # Users CRUD
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # Courses CRUD
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    
    # Enrollments
    path('enrollments/', views.enrollment_list, name='enrollment_list'),
    path('enrollments/<int:enrollment_id>/delete/', views.enrollment_delete, name='enrollment_delete'),
    
    # Likes
    path('likes/', views.like_list, name='like_list'),
    path('likes/<int:like_id>/delete/', views.like_delete, name='like_delete'),
    
    # Reviews
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/<int:review_id>/delete/', views.review_delete, name='review_delete'),
]
```

## adminpanel/views.py (continued)
```python
# [Previous views.py content continues from line 1378]

            )
            
            messages.success(request, f'Course "{course.title}" updated.')
            return redirect('adminpanel:course_list')
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
        'instructors': User.objects.filter(role='teacher').order_by('username'),
        'categories': Category.objects.all().order_by('name'),
        'title': 'Edit Course',
    }
    return render(request, 'adminpanel/course_form.html', context)


@admin_required
def course_delete(request, course_id):
    """Delete course"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Log course deletion
        from .middleware import ActivityLogger
        ActivityLogger.log_action(
            user=request.user,
            action_type='delete_course',
            object_type='course',
            object_id=course.id,
            object_repr=str(course),
            request=request
        )
        
        course.delete()
        messages.success(request, f'Course "{course.title}" deleted.')
        return redirect('adminpanel:course_list')
    
    context = {
        'course': course,
        'title': 'Delete Course',
    }
    return render(request, 'adminpanel/course_delete.html', context)


@admin_required
def enrollment_list(request):
    """Enrollment list"""
    enrollments = CourseEnrollment.objects.select_related('user', 'course').order_by('-enrolled_at')
    
    context = {
        'enrollments': enrollments,
        'title': 'Enrollment Management',
    }
    return render(request, 'adminpanel/enrollment_list.html', context)


@admin_required
def enrollment_delete(request, enrollment_id):
    """Delete enrollment"""
    enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id)
    
    if request.method == 'POST':
        enrollment.delete()
        messages.success(request, 'Enrollment deleted.')
        return redirect('adminpanel:enrollment_list')
    
    context = {
        'enrollment': enrollment,
        'title': 'Delete Enrollment',
    }
    return render(request, 'adminpanel/enrollment_delete.html', context)


@admin_required
def like_list(request):
    """Like list"""
    likes = CourseLike.objects.select_related('user', 'course').order_by('-created_at')
    
    context = {
        'likes': likes,
        'title': 'Like Management',
    }
    return render(request, 'adminpanel/like_list.html', context)


@admin_required
def like_delete(request, like_id):
    """Delete like"""
    like = get_object_or_404(CourseLike, id=like_id)
    
    if request.method == 'POST':
        like.delete()
        messages.success(request, 'Like deleted.')
        return redirect('adminpanel:like_list')
    
    context = {
        'like': like,
        'title': 'Delete Like',
    }
    return render(request, 'adminpanel/like_delete.html', context)


@admin_required
def review_list(request):
    """Review list"""
    reviews = CourseReview.objects.select_related('user', 'course').order_by('-created_at')
    
    context = {
        'reviews': reviews,
        'title': 'Review Management',
    }
    return render(request, 'adminpanel/review_list.html', context)


@admin_required
def review_delete(request, review_id):
    """Delete review"""
    review = get_object_or_404(CourseReview, id=review_id)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted.')
        return redirect('adminpanel:review_list')
    
    context = {
        'review': review,
        'title': 'Delete Review',
    }
    return render(request, 'adminpanel/review_delete.html', context)


@admin_required
def download_backup(request, filename):
    """Download backup"""
    from .backup_utils import SystemBackup
    
    backup_system = SystemBackup()
    
    if backup_system.backup_exists(filename):
        file_path = backup_system.get_backup_path(filename)
        
        try:
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        except Exception as e:
            messages.error(request, f'Error downloading backup: {str(e)}')
    else:
        messages.error(request, 'Backup file not found')
    
    return redirect('adminpanel:backup_logs')


@admin_required
def delete_backup(request, filename):
    """Delete backup"""
    from .backup_utils import SystemBackup
    
    backup_system = SystemBackup()
    
    if request.method == 'POST':
        if backup_system.delete_backup(filename, request.user):
            messages.success(request, f'Backup {filename} deleted.')
        else:
            messages.error(request, 'Error deleting backup')
    
    return redirect('adminpanel:backup_logs')


@admin_required
def restore_backup(request, filename):
    """Restore backup (placeholder)"""
    messages.info(request, f'Backup restoration for {filename} - feature not implemented yet')
    return redirect('adminpanel:backup_logs')
```

---

# CHAT MODULE

## chat/__init__.py
```python
```

## chat/admin.py
```python
from django.contrib import admin

# Register your models here.
```

## chat/apps.py
```python
from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
```

## chat/consumers.py
```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from .models import Message, SupportChat
from django.utils import timezone
from accounts.models import Notification

User = get_user_model()

predefined = {
    "How to choose a suitable course?": "To choose a course, consider your knowledge level, goals, and time. Look at course descriptions and reviews.",
    "Payment problem": "If you have a payment problem, check your card details or contact your bank. Courses are free, but premium features may require payment.",
}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Check if user has access to this chat
        try:
            chat = SupportChat.objects.get(id=self.chat_id)
            user = self.scope['user']
            if user != chat.user and user.role != 'admin':
                await self.close()
                return
        except SupportChat.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Filter out messages containing 'from'
        if 'from' in message.lower():
            return
        
        sender = self.scope['user']

        chat = SupportChat.objects.get(id=self.chat_id)
        msg = Message.objects.create(chat=chat, sender=sender, content=message)

        # Auto reply for predefined questions
        reply_text = None
        if msg.content in predefined:
            admin = chat.admin or User.objects.filter(role='admin').first()
            if admin:
                reply_text = predefined[msg.content]
                reply = Message.objects.create(chat=chat, sender=admin, content=reply_text)
                chat.updated_at = timezone.now()
                chat.save()
        elif msg.content == "Other problem":
            chat.priority = True
            chat.save()

        # Create notification for user if admin sent message
        if msg.sender.role == 'admin':
            Notification.objects.create(user=chat.user, message=f"Admin replied: {msg.content[:50]}...")
        
        # Create notification for admin if user sent message
        elif msg.sender == chat.user:
            admin = chat.admin or User.objects.filter(role='admin').first()
            if admin:
                Notification.objects.create(user=admin, message=f"New message in support from {msg.sender.username}: {msg.content[:50]}...")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.username,
                'sender_id': sender.id,
                'timestamp': str(msg.created_at)
            }
        )

        # Send auto reply if any
        if reply_text:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': reply_text,
                    'sender': admin.username,
                    'sender_id': admin.id,
                    'timestamp': str(reply.created_at)
                }
            )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        sender_id = event['sender_id']
        timestamp = event['timestamp']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'sender_id': sender_id,
            'timestamp': timestamp
        }))
```

## chat/models.py
```python
from django.db import models
from accounts.models import User

class SupportChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_chats')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='admin_chats')
    subject = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('closed', 'Closed')], default='open')
    priority = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat {self.id} - {self.user.username}"

class Message(models.Model):
    chat = models.ForeignKey(SupportChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"
```

## chat/routing.py
```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
```

## chat/tests.py
```python
from django.test import TestCase

# Create your tests here.
```

## chat/urls.py
```python
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('<int:chat_id>/send/', views.send_message, name='send_message'),
    path('start/', views.start_chat, name='start_chat'),
    path('<int:chat_id>/close/', views.close_chat, name='close_chat'),
]
```

## chat/views.py
```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import SupportChat, Message
from accounts.models import User

@login_required
def chat_list(request):
    if request.user.role == 'admin':
        chats = SupportChat.objects.all().order_by('-updated_at')
    else:
        chats = SupportChat.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'chat/chat_list.html', {'chats': chats})

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    # Access check
    if request.user.role != 'admin' and chat.user != request.user:
        messages.error(request, 'You do not have access to this chat')
        return redirect('chat:chat_list')
    
    messages_list = chat.messages.all().order_by('created_at')
    
    # Mark messages as read
    if request.user.role == 'admin':
        unread_messages = messages_list.filter(is_read=False).exclude(sender=request.user)
        unread_messages.update(is_read=True)
    else:
        unread_messages = messages_list.filter(is_read=False, sender__role='admin')
        unread_messages.update(is_read=True)
    
    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages': messages_list
    })

@login_required
@require_POST
def send_message(request, chat_id):
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    # Access check
    if request.user.role != 'admin' and chat.user != request.user:
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    content = request.POST.get('content')
    
    if content.strip():
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=content.strip()
        )
        chat.updated_at = message.created_at
        chat.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.created_at.strftime('%H:%M'),
                'sender': message.sender.username,
                'is_own': True
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Empty message'})

@login_required
def start_chat(request):
    if request.user.role == 'admin':
        messages.error(request, 'Administrators cannot create chats')
        return redirect('chat:chat_list')
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        if subject.strip():
            chat = SupportChat.objects.create(
                user=request.user,
                subject=subject.strip()
            )
            messages.success(request, 'Chat created')
            return redirect('chat:chat_detail', chat_id=chat.id)
    
    return render(request, 'chat/start_chat.html')

@login_required
@require_POST
def close_chat(request, chat_id):
    chat = get_object_or_404(SupportChat, id=chat_id)
    
    if request.user.role != 'admin':
        messages.error(request, 'Only administrator can close chat')
        return redirect('chat:chat_detail', chat_id=chat_id)
    
    chat.status = 'closed'
    chat.save()
    messages.success(request, 'Chat closed')
    return redirect('chat:chat_detail', chat_id=chat_id)
```

---

# COURSES MODULE

## courses/__init__.py
```python
```

## courses/admin.py
```python
from django.contrib import admin

# Register your models here.
```

## courses/apps.py
```python
from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
```

## courses/forms.py
```python
from django import forms
from .models import CourseReview


class CourseReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} \u2b50') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-input'}),
        label='Rating'
    )
    
    class Meta:
        model = CourseReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Your review about the course...'
            }),
        }
        labels = {
            'comment': 'Comment',
        }
```

## courses/models.py
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from urllib.parse import quote

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Name')
    description = models.TextField(blank=True, verbose_name='Description')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Instructor')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='Category')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner', verbose_name='Level')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Price')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True, verbose_name='Thumbnail')
    is_published = models.BooleanField(default=False, verbose_name='Published')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated')
    
    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
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
    title = models.CharField(max_length=200, verbose_name='Title')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name='Course')
    content = models.TextField(verbose_name='Content')
    video_url = models.URLField(blank=True, verbose_name='Video URL')
    order = models.PositiveIntegerField(default=0, verbose_name='Order')
    is_free = models.BooleanField(default=False, verbose_name='Free')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    
    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Course')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Enrollment Date')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Completion Date')
    progress = models.PositiveIntegerField(default=0, verbose_name='Progress (%)')
    
    class Meta:
        verbose_name = 'Course Enrollment'
        verbose_name_plural = 'Course Enrollments'
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class CourseLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='likes', verbose_name='Course')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date')
    
    class Meta:
        verbose_name = 'Like'
        verbose_name_plural = 'Likes'
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.username} liked {self.course.title}"

class CourseReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='User')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', verbose_name='Course')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Rating'
    )
    comment = models.TextField(verbose_name='Comment')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date')
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.course.title}"
```

## courses/tests.py
```python
from django.test import TestCase

# Create your tests here.
```

## courses/urls.py
```python
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/like/', views.toggle_like, name='toggle_like'),
    path('<int:course_id>/review/', views.submit_review, name='submit_review'),
    path('<int:course_id>/lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
]
```

## courses/views.py
```python
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
    
    # Filtering
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
    
    # Check if user is enrolled
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
        messages.success(request, f'You have enrolled in course "{course.title}"!')
    else:
        messages.info(request, f'You are already enrolled in course "{course.title}"')
    
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
        messages.success(request, 'Your review has been added!')
    else:
        messages.success(request, 'Your review has been updated!')
    
    return redirect('courses:course_detail', course_id=course_id)

@login_required
def lesson_view(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Check enrollment
    is_enrolled = CourseEnrollment.objects.filter(user=request.user, course=course).exists()
    if not is_enrolled and not lesson.is_free:
        messages.error(request, 'Enroll in the course to access lessons')
        return redirect('courses:course_detail', course_id=course_id)
    
    lessons = list(course.lessons.all().order_by('order'))
    current_index = lessons.index(lesson)
    
    prev_lesson = lessons[current_index - 1] if current_index > 0 else None
    next_lesson = lessons[current_index + 1] if current_index < len(lessons) - 1 else None
    
    # Update progress
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
```

---

# PROGAGE PROJECT CONFIGURATION

## progage/__init__.py
```python
```

## progage/asgi.py
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')

django_asgi_app = get_asgi_application()

# Import here to avoid import errors
try:
    from chat.routing import websocket_urlpatterns
except ImportError:
    websocket_urlpatterns = []

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

## progage/settings.py
```python
"""
Django settings for progage project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
from decouple import config
import dj_database_url

# Load environment variables from .env.local (if exists)
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).resolve().parent.parent / '.env.local'
    if env_file.exists():
        load_dotenv(env_file)
        print("Environment variables loaded from .env.local")
except ImportError:
    print("python-dotenv not installed, using default values")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-y&92ie9klnr&01t!pq#kg017f&)+78m_3#n+8r+)i0ejvie%#l')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

    # Get local IP and add to ALLOWED_HOSTS
import socket
try:
    local_ip = socket.gethostbyname(socket.gethostname())
    if not local_ip.startswith('127.'):
        allowed_hosts = f'localhost,127.0.0.1,{local_ip}'
    else:
        allowed_hosts = 'localhost,127.0.0.1'
except:
    allowed_hosts = 'localhost,127.0.0.1'

ALLOWED_HOSTS = ['*']
# CSRF Trusted Origins - for all possible development ports
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:55095',
    'http://127.0.0.1:55095',
    'https://*.lhr.life',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    # 'django_recaptcha',  # Disabled
    'django_otp',
    'django_otp.plugins.otp_totp',
    'accounts',
    'courses',
    'adminpanel',
    'chat',
    'channels',
    'rest_framework',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'rate_limit_middleware.GlobalRateLimitMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.BruteForceProtectionMiddleware',
    'adminpanel.middleware.LoggingMiddleware',
    'adminpanel.middleware.ExceptionLoggingMiddleware',
]

ROOT_URLCONF = 'progage.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 'accounts.context_processors.recaptcha_enabled',  # Disabled
            ],
        },
    },
]

WSGI_APPLICATION = 'progage.wsgi.application'

# ASGI
ASGI_APPLICATION = 'progage.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL', default='sqlite:///' + str(BASE_DIR / 'db.sqlite3')))
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # For real sending
EMAIL_HOST = 'smtp.gmail.com'  # Correct SMTP server for Gmail
EMAIL_PORT = 587  # Correct port for Gmail with TLS
EMAIL_HOST_USER = 'pashokbilashenko335@gmail.com'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # Gmail app password
EMAIL_USE_TLS = True  # Enable TLS
EMAIL_USE_SSL = False  # Disable SSL
EMAIL_TIMEOUT = 60  # Long timeout
EMAIL_USE_LOCALTIME = True  # Added for SMTP
DEFAULT_FROM_EMAIL = 'pashokbilashenko335@gmail.com'

# Password reset settings
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours in seconds

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration to suppress Channels INFO messages
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['console'],
    },
    'loggers': {
        'django.channels': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'daphne': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# Two-factor authentication settings
OTP_TOTP_ISSUER = 'Progage'
OTP_TOTP_VALIDITY = 30  # seconds
OTP_TOTP_DIGITS = 6

# Silenced system checks
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
```

## progage/urls.py
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('courses/', include('courses.urls')),
    path('chat/', include('chat.urls')),
    path('adminpanel/', include('adminpanel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

## progage/views.py
```python
from django.shortcuts import render

def home_view(request):
    context = {
        'current_year': 2026,
        'users_count': 1000,
        'courses_count': 50,
        'instructors_count': 25,
        'certificates_count': 500,
    }
    return render(request, 'home.html', context)
```

## progage/wsgi.py
```python
"""
WSGI config for progage project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')

application = get_wsgi_application()
```

---

# MAIN PROJECT FILES

## manage.py
```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

## requirements.txt
```
Django==5.1.0
djangorestframework==3.15.2
django-cors-headers==4.4.0
python-decouple==3.8
dj-database-url==2.2.0
Pillow==12.1.0
psycopg2-binary==2.9.11
mysqlclient==2.2.4
django-recaptcha==4.0.0
django-otp==1.7.0
qrcode[pil]==8.2
channels==4.1.0
channels-redis==4.2.0
daphne==4.1.2
gunicorn==21.2.0
whitenoise==6.6.0
```

---

# ADDITIONAL MIDDLEWARE

## rate_limit_middleware.py
```python
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time

class GlobalRateLimitMiddleware(MiddlewareMixin):
    """Global rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Apply rate limiting to all requests
        client_ip = self.get_client_ip(request)
        
        if self.is_rate_limited(client_ip):
            return HttpResponse(
                "Rate limit exceeded. Try again later.",
                status=429
            )
        
        if request.method == 'POST':
            self.record_request(client_ip)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, ip):
        # Check if IP exceeded rate limit (100 requests per minute)
        ip_key = f'rate_limit_{ip}'
        requests = cache.get(ip_key, 0)
        return requests >= 100
    
    def record_request(self, ip):
        # Record request with TTL 60 seconds
        ip_key = f'rate_limit_{ip}'
        if cache.get(ip_key) is None:
            cache.set(ip_key, 1, 60)
        else:
            cache.incr(ip_key)
```

---

# END OF UNIFIED PROJECT CODE
# All main modules and files have been integrated
```

# PROJECT SUMMARY

## Integrated Modules:
1. **accounts** - User authentication, profiles, 2FA
2. **adminpanel** - Admin dashboard, logging, backups, statistics  
3. **chat** - WebSocket chat system with support
4. **courses** - Course management, lessons, enrollment, reviews
5. **progage** - Main project configuration and URLs

## Key Features:
- Django 5.1 with REST Framework
- WebSocket real-time chat
- Two-factor authentication
- Comprehensive admin panel
- Rate limiting and security middleware
- Email system integration
- Database migrations
- Static/media file handling
- CORS support for frontend integration

## Security Features:
- Brute force protection
- Rate limiting middleware
- CSRF protection
- Two-factor authentication
- Activity logging
- Error tracking
- Session management

## Deployment Ready:
- ASGI/WSGI configuration
- Production settings support
- Environment variable configuration
- Database URL parsing
- Static files configuration
- Docker-ready structure
