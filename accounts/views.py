from django.shortcuts import render, redirect, get_object_or_404
import json
from django.db.models import Count, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.core.cache import cache
from django_otp import devices_for_user
from courses.models import Course, CourseEnrollment
from .forms import (
    UserRegistrationForm, UserUpdateForm, ProfileUpdateForm,
    CustomAuthenticationForm, CustomPasswordResetForm, TwoFactorForm, TwoFactorSetupForm, TeacherRatingForm
)
from .models import Profile, TeacherRating

User = get_user_model()

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
    form = CustomAuthenticationForm(request, data=request.POST or None)
    
    if request.method == 'POST':
        # Проверяем rate limiting перед обработкой формы
        client_ip = get_client_ip(request)
        username = request.POST.get('username', '')
        
        if is_rate_limited(client_ip, username):
            return HttpResponse(
                "Слишком много попыток. Попробуйте через 5 минут.",
                status=429
            )
        
        # Сначала проверяем пользователя
        try:
            user_obj = User.objects.get(username__iexact=username)
            
            # ЕСЛИ НЕАКТИВЕН
            if not user_obj.is_active:
                # УБИРАЕМ ОШИБКИ ФОРМЫ
                form.errors.clear()
                
                messages.error(
                    request,
                    'Ваш аккаунт неактивен. Обратитесь к администратору для активации.'
                )
                
                return render(request, 'accounts/login.html', {
                    'form': form
                })
                
        except User.DoesNotExist:
            pass
        
        # Только теперь authenticate
        user = authenticate(request, username=username, password=request.POST.get('password'))
        
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
        
        # УБИРАЕМ ОШИБКИ ФОРМЫ
        form.errors.clear()
        
        messages.error(
            request,
            'Неверное имя пользователя или пароль'
        )
        
        # Записываем неудачную попытку
        record_failed_attempt(client_ip, username)
    
    return render(request, 'accounts/login.html', {
        'form': form
    })


def password_reset_request(request):
    """Запрос на восстановление пароля"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='accounts/password_reset_email.txt',
                html_email_template_name='accounts/password_reset_email.html',
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
    """Отображение уведомлений пользователя"""
    from .models import Notification
    
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Помечаем все уведомления как прочитанные
    unread_count = user_notifications.filter(is_read=False).count()
    
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        user_notifications.update(is_read=True)
        messages.success(request, 'Все уведомления отмечены как прочитанные')
        return redirect('accounts:notifications')
    
    return render(request, 'accounts/notifications.html', {
        'notifications': user_notifications,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    """Отметить одно уведомление как прочитанное"""
    from .models import Notification
    
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        messages.success(request, 'Уведомление отмечено как прочитанное')
    except Notification.DoesNotExist:
        messages.error(request, 'Уведомление не найдено')
    
    return redirect('accounts:notifications')

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            
            # Сначала сохраняем profile_form
            profile_form.save()
            
            # Обрабатываем 2FA отдельно
            two_factor_enabled = request.POST.get('two_factor_enabled') == 'on'
            
            if two_factor_enabled != profile.two_factor_enabled:
                if two_factor_enabled:
                    # Убеждаемся, что TOTP устройство создано
                    device = profile.get_totp_device()
                    
                    backup_codes = profile.generate_backup_codes()
                    
                    # Принудительно устанавливаем значения
                    profile.two_factor_enabled = True
                    profile.backup_codes = backup_codes
                    profile.save()
                    
                    messages.success(request, 'Двухфакторная аутентификация включена. Резервные коды сгенерированы!')
                else:
                    # Выключаем 2FA - очищаем резервные коды
                    profile.two_factor_enabled = False
                    profile.backup_codes = []
                    profile.save()
                    
                    messages.info(request, 'Двухфакторная аутентификация отключена.')
            else:
                # Если статус не менялся, просто сохраняем текущее значение
                profile.two_factor_enabled = two_factor_enabled
                profile.save()
            
            if two_factor_enabled and not profile.backup_codes:
                messages.success(request, 'Ваш профиль был обновлен! Двухфакторная аутентификация включена.')
            elif not two_factor_enabled:
                messages.success(request, 'Ваш профиль был обновлен! Двухфакторная аутентификация отключена.')
            else:
                messages.success(request, 'Ваш профиль был обновлен!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    # Считаем количество курсов пользователя
    from courses.models import CourseEnrollment
    enrollment_count = CourseEnrollment.objects.filter(user=request.user).count()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'enrollment_count': enrollment_count
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
    
    # Расчет среднего прогресса
    total_enrollments = enrollments.count()
    if total_enrollments > 0:
        total_progress = sum(enrollment.progress or 0 for enrollment in enrollments)
        average_progress = total_progress // total_enrollments
    else:
        average_progress = 0
    
    # Получаем последнюю активность (когда пользователь обновлял прогресс)
    # Используем время последнего обновления progress или enrolled_at
    last_activity_enrollment = enrollments.order_by('-enrolled_at').first()
    if last_activity_enrollment:
        # Показываем enroll_at как последнюю активность (можно будет заменить на реальную активность)
        last_activity = last_activity_enrollment.enrolled_at
    else:
        last_activity = None
    
    context = {
        'enrollments': enrollments,
        'completed_count': enrollments.filter(progress=100).count(),
        'in_progress_count': enrollments.filter(progress__lt=100).count(),
        'average_progress': average_progress,
        'last_activity': last_activity,
        'last_enrollment': last_activity_enrollment,
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
    
    user = get_object_or_404(User, id=user_id)
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
            
            messages.success(request, 'Двухфакторная аутентификация включена. Сохраните резервные коды в надежном месте!')
            
        elif action == 'disable':
            # Turn off 2FA
            print(f"DEBUG: DISABLING 2FA - was {profile.two_factor_enabled}")
            profile.two_factor_enabled = False
            profile.backup_codes = []
            profile.save()
            print(f"DEBUG: 2FA disabled, now = {profile.two_factor_enabled}")
            messages.success(request, 'Двухфакторная аутентификация отключена.')
            
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

def teachers_list(request):
    """
    Страница со списком преподавателей с поиском
    """
    search_query = request.GET.get('search', '')
    
    # Базовый запрос для преподавателей (только с курсами)
    teachers = User.objects.filter(role='teacher', course__isnull=False).distinct().select_related('profile')
    
    # Применяем поиск если есть запрос
    if search_query:
        teachers = teachers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Добавляем статистику по курсам
    teachers = teachers.annotate(
        courses_count=Count('course', distinct=True),
        students_count=Count('course__enrollments', distinct=True)
    ).order_by('first_name', 'last_name')
    
    # Получаем информацию о курсах для каждого преподавателя
    teachers_data = []
    for teacher in teachers:
        courses = Course.objects.filter(instructor=teacher).select_related('category')
        courses_info = []
        for course in courses:
            courses_info.append({
                'title': course.title,
                'category': course.category.name if course.category else 'Без категории',
                'students': course.enrollment_count if hasattr(course, 'enrollment_count') else 0
            })
        teachers_data.append({
            'teacher': teacher,
            'courses': courses,
            'courses_info': courses_info
        })
    
    # Добавляем JSON данные для каждого преподавателя
    for teacher_data in teachers_data:
        teacher_data['courses_json'] = json.dumps(teacher_data['courses_info'])
    
    context = {
        'teachers_data': teachers_data,
        'search_query': search_query,
        'teachers_count': len(teachers_data)
    }
    
    return render(request, 'accounts/teachers_list.html', context)

def teacher_profile(request, teacher_id):
    try:
        teacher = User.objects.get(id=teacher_id, role='teacher')
    except User.DoesNotExist:
        raise Http404("Преподаватель не найден")
    
    # Получаем курсы преподавателя
    courses = Course.objects.filter(instructor=teacher).select_related('category')
    
    # Получаем оценки преподавателя
    teacher_ratings = TeacherRating.objects.filter(teacher=teacher).select_related('student')
    
    # Считаем статистику оценок
    total_teacher_ratings = teacher_ratings.count()
    teacher_average_rating = 0
    if total_teacher_ratings > 0:
        try:
            teacher_average_rating = round(sum(rating.rating for rating in teacher_ratings) / total_teacher_ratings, 1)
        except (ValueError, TypeError):
            teacher_average_rating = 0
    
    # Распределение оценок
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating in teacher_ratings:
        rating_distribution[rating.rating] += 1
    
    # Проверяем, может ли текущий пользователь оценить
    can_rate = False
    user_rating = None
    if request.user.is_authenticated and request.user.role == 'student':
        # Проверяем, записан ли студент на курсы преподавателя
        student_enrollments = CourseEnrollment.objects.filter(
            user=request.user,
            course__instructor=teacher
        ).exists()
        
        if student_enrollments:
            can_rate = True
            try:
                user_rating = TeacherRating.objects.get(student=request.user, teacher=teacher)
            except TeacherRating.DoesNotExist:
                user_rating = None
    
    # Обработка формы оценки
    if request.method == 'POST' and can_rate:
        form = TeacherRatingForm(request.POST)
        if form.is_valid():
            try:
                if user_rating:
                    # Обновляем существующую оценку
                    user_rating.rating = form.cleaned_data['rating']
                    user_rating.comment = form.cleaned_data['comment']
                    user_rating.save()
                    if not any('Ваша оценка успешно обновлена!' in str(message) for message in messages.get_messages(request)):
                        messages.success(request, 'Ваша оценка успешно обновлена!')
                else:
                    # Создаем новую оценку
                    rating = form.save(commit=False)
                    rating.student = request.user
                    rating.teacher = teacher
                    rating.save()
                    if not any('Ваша оценка успешно сохранена!' in str(message) for message in messages.get_messages(request)):
                        messages.success(request, 'Ваша оценка успешно сохранена!')
                return redirect('accounts:teacher_profile', teacher_id=teacher_id)
            except Exception as e:
                # Обработка ошибки уникальности
                if 'UNIQUE constraint' in str(e) or 'уже существует' in str(e):
                    form.add_error(None, 'Вы уже оценивали этого преподавателя. Вы можете изменить свою оценку.')
                else:
                    form.add_error(None, 'Произошла ошибка при сохранении оценки.')
        else:
            form = TeacherRatingForm(instance=user_rating)
    else:
        form = TeacherRatingForm(instance=user_rating)
    
    # Считаем базовую статистику
    total_students = 0
    total_likes = 0
    total_reviews = 0
    total_rating = 0
    courses_with_stats = []
    
    for course in courses:
        try:
            student_count = course.enrollments.count()
        except:
            student_count = 0
            
        try:
            likes_count = course.likes.count()
        except:
            likes_count = 0
            
        try:
            reviews_count = course.reviews.count()
        except:
            reviews_count = 0
        
        # Считаем средний рейтинг курса
        course_rating = 0
        try:
            if reviews_count > 0:
                ratings = []
                for review in course.reviews.all():
                    if hasattr(review, 'rating'):
                        ratings.append(review.rating)
                if ratings:
                    course_rating = round(sum(ratings) / len(ratings), 1)
        except:
            course_rating = 0
        
        total_students += student_count
        total_likes += likes_count
        total_reviews += reviews_count
        total_rating += course_rating
        
        courses_with_stats.append({
            'course': course,
            'enrollment_count': student_count,
            'likes_count': likes_count,
            'reviews_count': reviews_count,
            'rating': course_rating
        })
    
    # Дополнительная статистика
    try:
        published_courses = courses.filter(status='published').count()
    except:
        published_courses = courses.count()
        
    try:
        draft_courses = courses.filter(status='draft').count()
    except:
        draft_courses = 0
    
    # Средний рейтинг по всем курсам
    average_rating = round(total_rating / courses.count(), 1) if courses.count() > 0 else 0
    
    # Сортируем курсы по популярности (по количеству студентов)
    popular_courses = sorted(courses_with_stats, key=lambda x: x['enrollment_count'], reverse=True)[:3]
    
    # Последние оценки
    recent_ratings = teacher_ratings[:5]
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'courses_with_stats': courses_with_stats,
        'teacher_ratings': teacher_ratings,
        'total_courses': courses.count(),
        'published_courses': published_courses,
        'draft_courses': draft_courses,
        'total_students': total_students,
        'total_likes': total_likes,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'teacher_average_rating': teacher_average_rating,
        'total_teacher_ratings': total_teacher_ratings,
        'rating_distribution': rating_distribution,
        'average_students_per_course': round(total_students / courses.count(), 1) if courses.count() > 0 else 0,
        'popular_courses': popular_courses,
        'recent_ratings': recent_ratings,
        'can_rate': can_rate,
        'user_rating': user_rating,
        'form': form,
    }
    
    return render(request, 'accounts/teacher_profile.html', context)

def test_stars(request):
    return render(request, 'accounts/test_stars.html')

def certificates(request):
    return render(request, 'accounts/certificates.html')

@login_required
def settings(request):
    """Страница настроек профиля"""
    if request.method == 'POST':
        # Обработка обновления профиля
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.bio = request.POST.get('bio', user.bio)
        
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        user.save()
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('accounts:settings')
    
    return render(request, 'accounts/settings.html')

@login_required
def generate_2fa_secret(request):
    """Генерация секретного ключа для 2FA"""
    if request.method == 'POST':
        import pyotp
        import qrcode
        from io import BytesIO
        import base64
        
        user = request.user
        profile = user.profile
        
        # Генерируем секретный ключ
        secret = pyotp.random_base32()
        
        # Сохраняем временно в сессии
        request.session['2fa_secret'] = secret
        
        # Создаем provisioning URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name='Progage'
        )
        
        # Генерируем QR код
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return JsonResponse({
            'success': True,
            'secret': secret,
            'qr_code_url': f'data:image/png;base64,{qr_base64}'
        })
    
    return JsonResponse({'success': False})

@login_required
def verify_2fa_setup(request):
    """Проверка кода при настройке 2FA"""
    if request.method == 'POST':
        import pyotp
        
        try:
            data = json.loads(request.body)
            code = data.get('code')
            secret = request.session.get('2fa_secret')
            
            if not secret:
                return JsonResponse({'success': False, 'error': 'Секретный ключ не найден'})
            
            # Проверяем код
            totp = pyotp.TOTP(secret)
            if totp.verify(code):
                # Генерируем резервные коды
                profile = request.user.profile
                backup_codes = profile.generate_backup_codes()
                
                return JsonResponse({
                    'success': True,
                    'backup_codes': backup_codes
                })
            else:
                return JsonResponse({'success': False, 'error': 'Неверный код'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False})

@login_required
def enable_2fa(request):
    """Включение 2FA"""
    if request.method == 'POST':
        profile = request.user.profile
        secret = request.session.get('2fa_secret')
        
        if not secret:
            return JsonResponse({'success': False, 'error': 'Секретный ключ не найден'})
        
        # Получаем или создаем TOTP устройство
        device = profile.get_totp_device()
        
        # Обновляем секретный ключ устройства
        device.key = secret
        device.save()
        
        # Включаем 2FA
        profile.two_factor_enabled = True
        profile.save()
        
        # Очищаем сессию
        del request.session['2fa_secret']
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def disable_2fa(request):
    """Отключение 2FA"""
    if request.method == 'POST':
        profile = request.user.profile
        
        # Отключаем 2FA
        profile.two_factor_enabled = False
        profile.backup_codes = []
        profile.save()
        
        # Удаляем TOTP устройства
        from django_otp.plugins.otp_totp.models import TOTPDevice
        TOTPDevice.objects.filter(user=request.user).delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def regenerate_backup_codes(request):
    """Перегенерация резервных кодов"""
    if request.method == 'POST':
        profile = request.user.profile
        backup_codes = profile.generate_backup_codes()
        
        return JsonResponse({
            'success': True,
            'backup_codes': backup_codes
        })
    
    return JsonResponse({'success': False})

@login_required
def reset_2fa(request):
    """Полный сброс 2FA"""
    if request.method == 'POST':
        profile = request.user.profile
        
        # Отключаем 2FA
        profile.two_factor_enabled = False
        profile.backup_codes = []
        profile.save()
        
        # Удаляем TOTP устройства
        from django_otp.plugins.otp_totp.models import TOTPDevice
        TOTPDevice.objects.filter(user=request.user).delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def change_password(request):
    """Смена пароля"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Проверяем текущий пароль
        if not request.user.check_password(current_password):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Неверный текущий пароль'})
            else:
                messages.error(request, 'Неверный текущий пароль')
                return redirect('accounts:settings')
        
        # Проверяем совпадение новых паролей
        if new_password != confirm_password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Новые пароли не совпадают'})
            else:
                messages.error(request, 'Новые пароли не совпадают')
                return redirect('accounts:settings')
        
        # Проверяем длину пароля
        if len(new_password) < 8:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Пароль должен содержать минимум 8 символов'})
            else:
                messages.error(request, 'Пароль должен содержать минимум 8 символов')
                return redirect('accounts:settings')
        
        # Меняем пароль
        request.user.set_password(new_password)
        request.user.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Пароль успешно изменен')
            return redirect('accounts:settings')
    
    return redirect('accounts:settings')

@login_required
def logout_all(request):
    """Выход из всех устройств"""
    if request.method == 'POST':
        # Удаляем все сессии пользователя кроме текущей
        from django.contrib.sessions.models import Session
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Получаем все сессии пользователя
        sessions = Session.objects.filter(
            session_data__contains=str(request.user.id)
        ).exclude(session_key=request.session.session_key)
        
        # Удаляем сессии
        sessions.delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def update_notifications(request):
    """Обновление настроек уведомлений"""
    if request.method == 'POST':
        user = request.user
        
        # Получаем или создаем настройки уведомлений
        if not hasattr(user, 'notification_settings'):
            from .models import UserNotifications
            UserNotifications.objects.create(user=user)
            user.refresh_from_db()
        
        # Обновляем настройки
        notifications = user.notification_settings
        notifications.support_messages = 'support_messages' in request.POST
        notifications.new_lessons = 'new_lessons' in request.POST
        notifications.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Настройки уведомлений сохранены')
            return redirect('accounts:settings')
    
    return redirect('accounts:settings')


@login_required
def disable_2fa(request):
    """Отключение двухфакторной аутентификации"""
    if request.method == 'POST':
        profile = request.user.profile
        profile.two_factor_enabled = False
        profile.two_factor_secret = ''
        profile.save()
        
        messages.success(request, 'Двухфакторная аутентификация отключена')
        return redirect('accounts:settings')
    
    return redirect('accounts:settings')

@login_required
def update_privacy(request):
    """Обновление настроек приватности"""
    if request.method == 'POST':
        user = request.user
        
        # Получаем или создаем настройки приватности
        if not hasattr(user, 'privacy_settings'):
            from .models import UserPrivacy
            UserPrivacy.objects.create(user=user)
            user.refresh_from_db()
        
        # Обновляем настройки
        privacy = user.privacy_settings
        privacy.public_profile = 'public_profile' in request.POST
        privacy.show_email = 'show_email' in request.POST
        privacy.show_progress = 'show_progress' in request.POST
        privacy.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        else:
            messages.success(request, 'Настройки приватности сохранены')
            return redirect('accounts:settings')
    
    return redirect('accounts:settings')
