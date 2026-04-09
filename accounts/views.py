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
            messages.success(request, f'Аккаунт создан для {username}!')
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Проверяем rate limiting перед обработкой формы
        client_ip = get_client_ip(request)
        username = request.POST.get('username', '')
        
        if is_rate_limited(client_ip, username):
            return HttpResponse(
                "Слишком много попыток. Попробуйте через 5 минут.",
                status=429
            )
        
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # В проекте USERNAME_FIELD = 'email', поэтому authenticate ожидает email в параметре username.
            user = authenticate(username=username, password=password)

            # Поддержка входа по username: если ввели не email, пробуем найти пользователя по username
            # и авторизоваться по его email.
            if user is None and username and '@' not in username:
                try:
                    u = UserModel.objects.get(username__iexact=username)
                    user = authenticate(username=u.email, password=password)
                except UserModel.DoesNotExist:
                    user = None
                    
            if user is not None:
                # Проверяем включена ли 2FA
                try:
                    profile = user.profile
                    if profile.two_factor_enabled:
                        # Сохраняем пользователя в сессии для 2FA проверки
                        request.session['2fa_user_id'] = user.id
                        return redirect('accounts:two_factor_verify')
                except Profile.DoesNotExist:
                    pass
                
                # Сбрасываем счетчик попыток при успешном входе
                reset_login_attempts(client_ip, username)
                login(request, user)
                messages.info(request, f'Вы вошли как {username}')
                return redirect('home')
            else:
                # Записываем неудачную попытку
                record_failed_attempt(client_ip, username)
                messages.error(request, 'Неверное имя пользователя или пароль')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
            return render(request, 'accounts/login.html', {'form': form})
    form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def password_reset_request(request):
    """Запрос на восстановление пароля"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='accounts/password_reset_email.html',
                subject_template_name='accounts/password_reset_subject.txt',
            )
            messages.success(request, 'Инструкции по восстановлению пароля отправлены на вашу почту.')
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
    """Проверяем, не превышен ли лимит попыток"""
    ip_key = f'login_attempts_ip_{ip}'
    user_key = f'login_attempts_user_{username}_{ip}' if username else None
    
    ip_attempts = cache.get(ip_key, 0)
    user_attempts = cache.get(user_key, 0) if user_key else 0
    
    return ip_attempts >= 5 or user_attempts >= 3

def record_failed_attempt(ip, username=''):
    """Записываем неудачную попытку"""
    ip_key = f'login_attempts_ip_{ip}'
    user_key = f'login_attempts_user_{username}_{ip}' if username else None
    
    # Безопасный инкремент с инициализацией
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
    """Сбрасываем счетчик попыток при успешном входе"""
    ip_key = f'login_attempts_ip_{ip}'
    user_key = f'login_attempts_user_{username}_{ip}' if username else None
    
    cache.delete(ip_key)
    if user_key:
        cache.delete(user_key)


@login_required
def notifications(request):
    # В проекте есть шаблон notifications.html, но модели/логики уведомлений пока нет.
    # Возвращаем пустой список, чтобы страница и навигация работали.
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
            
            # Сначала сохраняем profile_form
            profile_form.save()
            
            # Обрабатываем 2FA отдельно
            two_factor_enabled = request.POST.get('two_factor_enabled') == 'on'
            
            # Отладочная информация
            print(f"DEBUG: two_factor_enabled = {two_factor_enabled}")
            print(f"DEBUG: POST data = {request.POST}")
            print(f"DEBUG: profile.two_factor_enabled (before) = {profile.two_factor_enabled}")
            
            if two_factor_enabled != profile.two_factor_enabled:
                if two_factor_enabled:
                    # Убеждаемся, что TOTP устройство создано
                    device = profile.get_totp_device()
                    print(f"DEBUG: TOTP device created = {device}")
                    
                    # Включаем 2FA - генерируем резервные коды
                    backup_codes = profile.generate_backup_codes()
                    print(f"DEBUG: Backup codes generated = {backup_codes}")
                    
                    # Принудительно устанавливаем значения
                    profile.two_factor_enabled = True
                    profile.backup_codes = backup_codes
                    profile.save()
                    
                    messages.success(request, 'Двухфакторная аутентификация включена. Резервные коды сгенерированы!')
                    print(f"DEBUG: profile.two_factor_enabled (after) = {profile.two_factor_enabled}")
                else:
                    # Выключаем 2FA - очищаем резервные коды
                    profile.two_factor_enabled = False
                    profile.backup_codes = []
                    profile.save()
                    
                    messages.info(request, 'Двухфакторная аутентификация отключена.')
                    print(f"DEBUG: 2FA disabled")
            else:
                # Если статус не менялся, просто сохраняем текущее значение
                profile.two_factor_enabled = two_factor_enabled
                profile.save()
                print(f"DEBUG: No change in 2FA status")
            
            if two_factor_enabled and not profile.backup_codes:
                messages.success(request, 'Ваш профиль был обновлен! Двухфакторная аутентификация включена.')
            elif not two_factor_enabled:
                messages.success(request, 'Ваш профиль был обновлен! Двухфакторная аутентификация отключена.')
            else:
                messages.success(request, 'Ваш профиль был обновлен!')
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
    messages.info(request, 'Вы вышли из системы')
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
        messages.error(request, 'Доступ только для преподавателей')
        return redirect('home')
    
    courses = Course.objects.filter(instructor=request.user)
    context = {
        'courses': courses,
        'total_students': sum(course.enrollment_count for course in courses),
    }
    return render(request, 'accounts/teacher_dashboard.html', context)

def two_factor_verify(request):
    """Проверка двухфакторного кода"""
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
            
            # Проверяем TOTP код
            if code:
                device = profile.get_totp_device()
                if device.verify_token(code):
                    # Успешная проверка 2FA
                    del request.session['2fa_user_id']
                    login(request, user)
                    messages.success(request, 'Вы успешно вошли в систему!')
                    return redirect('home')
                else:
                    messages.error(request, 'Неверный код из приложения')
            
            # Проверяем резервный код
            elif backup_code:
                if profile.verify_backup_code(backup_code):
                    # Успешная проверка резервного кода
                    del request.session['2fa_user_id']
                    login(request, user)
                    messages.success(request, 'Вы успешно вошли в систему с использованием резервного кода!')
                    messages.warning(request, 'Рекомендуется сгенерировать новые резервные коды в профиле.')
                    return redirect('home')
                else:
                    messages.error(request, 'Неверный резервный код')
            else:
                messages.error(request, 'Введите код из приложения или резервный код')
    else:
        form = TwoFactorForm()
    
    return render(request, 'accounts/two_factor_verify.html', {
        'form': form,
        'user': user
    })

@login_required
def two_factor_setup(request):
    """Настройка двухфакторной аутентификации"""
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
            # Перегенерируем резервные коды
            profile.backup_codes = profile.generate_backup_codes()
            profile.save()
            messages.success(request, 'Резервные коды обновлены.')
            
        return redirect('accounts:profile')
    
    # Получаем QR код для настройки
    device = profile.get_totp_device()
    qr_code_url = device.config_url
    
    return render(request, 'accounts/two_factor_setup.html', {
        'device': device,
        'qr_code_url': qr_code_url,
        'backup_codes': profile.backup_codes if profile.backup_codes else None
    })
