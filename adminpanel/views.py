from django.shortcuts import render, get_object_or_404, redirect

from django.contrib import messages

from django.db import models
from django.db.models import Count, Q, F

from django.contrib.auth import get_user_model

from django.urls import reverse

from django.utils import timezone

from datetime import timedelta

from django.http import JsonResponse, HttpResponse

from django.core.paginator import Paginator

from .decorators import admin_required

from .models import ActivityLog, SystemLog, BackupLog, UserSession, PopularContent, ErrorLog

from accounts.models import User

from courses.models import Course, CourseEnrollment, CourseLike, CourseReview, Lesson, Category



User = get_user_model()





@admin_required

def dashboard(request):

    """Главная страница админ-панели с расширенной статистикой"""

    # Базовая статистика

    stats = {

        'total_users': User.objects.count(),

        'students': User.objects.filter(role='student').count(),

        'authors': User.objects.filter(role='author').count(),

        'admins': User.objects.filter(role='admin').count(),

        'total_courses': Course.objects.count(),

        'total_enrollments': CourseEnrollment.objects.count(),

        'total_likes': CourseLike.objects.count(),

        'total_reviews': CourseReview.objects.count(),

    }

    

    # Активность за последние 7 дней

    week_ago = timezone.now() - timedelta(days=7)

    recent_stats = {

        'new_users': User.objects.filter(date_joined__gte=week_ago).count(),

        'active_users': UserSession.objects.filter(

            last_activity__gte=week_ago

        ).values('user').distinct().count(),

        'new_enrollments': CourseEnrollment.objects.filter(

            enrolled_at__gte=week_ago

        ).count(),

        'new_courses': Course.objects.filter(created_at__gte=week_ago).count(),

    }

    

    # Популярные курсы

    popular_courses = Course.objects.annotate(

        enrollments_total=Count('enrollments'),

        like_count=Count('likes')

    ).order_by('-enrollments_total', '-like_count')[:5]

    

    # Последние действия

    recent_activities = ActivityLog.objects.select_related('user').order_by('-action_time')[:10]

    

    # Ошибки за последние 24 часа

    day_ago = timezone.now() - timedelta(hours=24)

    recent_errors = ErrorLog.objects.filter(timestamp__gte=day_ago).count()

    

    context = {

        'stats': stats,

        'recent_stats': recent_stats,

        'popular_courses': popular_courses,

        'recent_activities': recent_activities,

        'recent_errors': recent_errors,

        'title': 'Админ-панель',

    }

    return render(request, 'adminpanel/dashboard.html', context)





# Логи активности

@admin_required

def activity_logs(request):

    """Просмотр логов активности"""

    logs = ActivityLog.objects.select_related('user').order_by('-action_time')

    

    # Фильтры

    action_type = request.GET.get('action_type')

    user_filter = request.GET.get('user')

    date_from = request.GET.get('date_from')

    date_to = request.GET.get('date_to')

    

    if action_type:

        logs = logs.filter(action_type=action_type)

    if user_filter:

        logs = logs.filter(user__username__icontains=user_filter)

    if date_from:

        logs = logs.filter(action_time__gte=date_from)

    if date_to:

        logs = logs.filter(action_time__lte=date_to)

    

    # Пагинация

    paginator = Paginator(logs, 50)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    

    context = {

        'page_obj': page_obj,

        'action_types': ActivityLog.ACTION_TYPES,

        'title': 'Логи активности',

    }

    return render(request, 'adminpanel/activity_logs.html', context)





# Системные логи

@admin_required

def system_logs(request):

    """Просмотр системных логов"""

    logs = SystemLog.objects.order_by('-timestamp')

    

    # Подсчет статистики по уровням

    log_counts = {

        'error': logs.filter(level='ERROR').count(),

        'warning': logs.filter(level='WARNING').count(),

        'info': logs.filter(level='INFO').count(),

        'debug': logs.filter(level='DEBUG').count(),

        'critical': logs.filter(level='CRITICAL').count(),

    }

    

    # Фильтры

    level = request.GET.get('level')

    module = request.GET.get('module')

    date_from = request.GET.get('date_from')

    date_to = request.GET.get('date_to')

    

    if level:

        logs = logs.filter(level=level)

    if module:

        logs = logs.filter(module__icontains=module)

    if date_from:

        logs = logs.filter(timestamp__gte=date_from)

    if date_to:

        logs = logs.filter(timestamp__lte=date_to)

    

    # Пагинация

    paginator = Paginator(logs, 50)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    

    context = {

        'page_obj': page_obj,

        'log_levels': SystemLog.LOG_LEVELS,

        'log_counts': log_counts,

        'title': 'Системные логи',

    }

    return render(request, 'adminpanel/system_logs.html', context)





# Логи ошибок

@admin_required

def error_logs(request):

    """Просмотр логов ошибок"""

    logs = ErrorLog.objects.select_related('user').order_by('-timestamp')

    

    # Фильтры

    error_type = request.GET.get('error_type')

    resolved = request.GET.get('resolved')

    date_from = request.GET.get('date_from')

    date_to = request.GET.get('date_to')

    

    if error_type:

        logs = logs.filter(error_type=error_type)

    if resolved is not None:

        logs = logs.filter(resolved=resolved == 'true')

    if date_from:

        logs = logs.filter(timestamp__gte=date_from)

    if date_to:

        logs = logs.filter(timestamp__lte=date_to)

    

    # Пагинация

    paginator = Paginator(logs, 50)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    

    context = {

        'page_obj': page_obj,

        'error_types': ErrorLog.ERROR_TYPES,

        'title': 'Логи ошибок',

    }

    return render(request, 'adminpanel/error_logs.html', context)





@admin_required

def resolve_error(request, error_id):

    """Отметить ошибку как решенную"""

    error = get_object_or_404(ErrorLog, id=error_id)

    if request.method == 'POST':

        error.resolved = True

        error.resolved_at = timezone.now()

        error.resolved_by = request.user

        error.save()

        

        messages.success(request, f'Ошибка #{error_id} отмечена как решенная')

        return redirect('adminpanel:error_logs')

    

    context = {

        'error': error,

        'title': 'Решение ошибки',

    }

    return render(request, 'adminpanel/resolve_error.html', context)





# Сессии пользователей

@admin_required

def user_sessions(request):

    """Просмотр активных сессий"""

    sessions = UserSession.objects.select_related('user').order_by('-last_activity')

    

    # Фильтры

    user_filter = request.GET.get('user')

    is_active = request.GET.get('active')

    

    if user_filter:

        sessions = sessions.filter(user__username__icontains=user_filter)

    if is_active is not None:

        sessions = sessions.filter(is_active=is_active == 'true')

    

    # Пагинация

    paginator = Paginator(sessions, 50)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    

    context = {

        'page_obj': page_obj,

        'title': 'Сессии пользователей',

    }

    return render(request, 'adminpanel/user_sessions.html', context)





# Популярный контент

@admin_required

def popular_content(request):

    """Просмотр популярного контента"""

    # Получаем все курсы с их статистикой

    courses = Course.objects.annotate(

        enrollments_total=models.Count('enrollments'),

        like_count=models.Count('likes')

    ).annotate(

        popularity_score=F('enrollments_total') * 10 + F('like_count') * 7

    ).order_by('-popularity_score')

    

    # Фильтры (оставляем задел под будущие типы контента, но сейчас фильтр по несуществующему полю убран)

    

    # Пагинация

    paginator = Paginator(courses, 50)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    

    context = {

        'page_obj': page_obj,

        'content_types': [

            ('course', 'Курсы'),

            ('lesson', 'Уроки'),

            ('all', 'Все'),

        ],

        'title': 'Популярный контент',

    }

    return render(request, 'adminpanel/popular_content.html', context)





# Бэкапы

@admin_required

def backup_logs(request):

    """Просмотр логов бэкапов"""

    logs = BackupLog.objects.select_related('created_by').order_by('-started_at')

    

    # Фильтры

    status = request.GET.get('status')

    backup_type = request.GET.get('backup_type')

    date_from = request.GET.get('date_from')

    date_to = request.GET.get('date_to')

    

    if status:

        logs = logs.filter(status=status)

    if backup_type:

        logs = logs.filter(backup_type=backup_type)

    if date_from:

        logs = logs.filter(started_at__gte=date_from)

    if date_to:

        logs = logs.filter(started_at__lte=date_to)

    

    # Пагинация

    paginator = Paginator(logs, 50)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    

    context = {

        'page_obj': page_obj,

        'status_choices': BackupLog.STATUS_CHOICES,

        'title': 'Логи бэкапов',

    }

    return render(request, 'adminpanel/backup_logs.html', context)





@admin_required

def create_backup(request):

    """Создание бэкапа"""

    if request.method == 'POST':

        backup_type = request.POST.get('backup_type', 'full')

        description = request.POST.get('description', '')

        

        # Создаем запись о начале бэкапа

        backup_log = BackupLog.objects.create(

            backup_type=backup_type,

            status='started',

            created_by=request.user,

            description=description

        )

        

        try:

            # Здесь будет логика создания бэкапа

            # import subprocess

            # result = subprocess.run(['python', 'manage.py', 'dbbackup'], 

            #                         capture_output=True, text=True)

            

            # Временно имитируем успешное создание

            backup_log.status = 'completed'

            backup_log.completed_at = timezone.now()

            backup_log.file_path = f'/backups/backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.sql'

            backup_log.file_size = 1024 * 1024  # 1MB

            backup_log.tables_count = 10

            backup_log.records_count = 1000

            backup_log.save()

            

            messages.success(request, f'Бэкап успешно создан: {backup_log.file_path}')

            

        except Exception as e:

            backup_log.status = 'failed'

            backup_log.error_message = str(e)

            backup_log.save()

            

            messages.error(request, f'Ошибка при создании бэкапа: {str(e)}')

        

        return redirect('adminpanel:backup_logs')

    

    context = {

        'title': 'Создание бэкапа',

    }

    return render(request, 'adminpanel/create_backup.html', context)





@admin_required

def download_backup(request, backup_id):

    """Скачивание бэкапа"""

    backup = get_object_or_404(BackupLog, id=backup_id)

    

    if backup.file_path and backup.status == 'completed':

        # Здесь будет логика скачивания файла

        messages.success(request, 'Начало скачивания бэкапа')

    else:

        messages.error(request, 'Файл бэкапа не найден или бэкап не завершен')

    

    return redirect('adminpanel:backup_logs')





# Статистика

@admin_required

def statistics(request):

    """Подробная статистика"""

    # Период для статистики

    days = int(request.GET.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)

    month_start = timezone.now() - timedelta(days=30)

    

    # Базовая статистика

    stats = {

        'users': User.objects.count(),

        'courses': Course.objects.count(),

        'lessons': Lesson.objects.count(),

        'enrollment_count': CourseEnrollment.objects.count(),

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

    

    # Ежемесячный рост

    monthly_growth = {

        'users': User.objects.filter(date_joined__gte=month_start).count(),

        'courses': Course.objects.filter(created_at__gte=month_start).count(),

        'lessons': Lesson.objects.filter(created_at__gte=month_start).count(),

        'enrollments': CourseEnrollment.objects.filter(enrolled_at__gte=month_start).count(),

        'likes': CourseLike.objects.filter(created_at__gte=month_start).count(),

        'reviews': CourseReview.objects.filter(created_at__gte=month_start).count(),

        'messages': Message.objects.filter(timestamp__gte=month_start).count(),

        'chats': SupportChat.objects.filter(created_at__gte=month_start).count(),

    }

    

    # Пользователи по ролям

    user_roles = {

        'students_count': User.objects.filter(role='student').count(),

        'authors_count': User.objects.filter(role='author').count(),

        'admins_count': User.objects.filter(role='admin').count(),

    }

    

    # Курсы по уровню сложности

    difficulty_levels = {

        'beginner_courses': Course.objects.filter(level='beginner').count(),

        'intermediate_courses': Course.objects.filter(level='intermediate').count(),

        'advanced_courses': Course.objects.filter(level='advanced').count(),

    }

    

    # Курсы по языкам программирования

    programming_languages = list(

        Course.objects.values('programming_language')

        .annotate(count=Count('id'))

        .order_by('-count')[:8]

    )

    

    # Топ курсы по популярности

    top_courses = list(

        Course.objects.annotate(

            enrollment_count=Count('enrollments'),

            like_count=Count('likes')

        ).annotate(

            popularity_score=F('enrollment_count') * 10 + F('like_count') * 7

        ).order_by('-popularity_score')[:10]

    )

    

    # Регистрация пользователей по месяцам за год

    user_registrations = []

    course_creations = []

    months_labels = []

    

    for i in range(12):

        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)

        month_end = month_start + timedelta(days=30)

        

        user_registrations.append(

            User.objects.filter(date_joined__gte=month_start, date_joined__lt=month_end).count()

        )

        course_creations.append(

            Course.objects.filter(created_at__gte=month_start, created_at__lt=month_end).count()

        )

        months_labels.append(month_start.strftime('%b'))

    

    # Активность по дням недели

    weekday_activity = []

    weekday_labels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

    

    for day in range(7):

        weekday_activity.append(

            ActivityLog.objects.filter(

                action_time__week_day=day+1

            ).count()

        )

    

    # Процентные соотношения

    total_items = sum([

        stats['users'], stats['courses'], stats['lessons'], 

        stats['enrollments'], stats['likes'], stats['reviews']

    ])

    

    percentages = {

        'user_percentage': round((stats['users'] / total_items) * 100, 1) if total_items > 0 else 0,

        'course_percentage': round((stats['courses'] / total_items) * 100, 1) if total_items > 0 else 0,

        'lesson_percentage': round((stats['lessons'] / total_items) * 100, 1) if total_items > 0 else 0,

        'enrollment_percentage': round((stats['enrollments'] / total_items) * 100, 1) if total_items > 0 else 0,

        'like_percentage': round((stats['likes'] / total_items) * 100, 1) if total_items > 0 else 0,

        'review_percentage': round((stats['reviews'] / total_items) * 100, 1) if total_items > 0 else 0,

        'message_percentage': round((stats['messages'] / total_items) * 100, 1) if total_items > 0 else 0,

        'chat_percentage': round((stats['support_chats'] / total_items) * 100, 1) if total_items > 0 else 0,

    }

    

    # Объединяем всю статистику

    stats.update({

        # Ежемесячный рост

        'monthly_users_growth': monthly_growth['users'],

        'monthly_courses_growth': monthly_growth['courses'],

        'monthly_lessons_growth': monthly_growth['lessons'],

        'monthly_enrollments_growth': monthly_growth['enrollments'],

        'monthly_likes_growth': monthly_growth['likes'],

        'monthly_reviews_growth': monthly_growth['reviews'],

        'monthly_messages_growth': monthly_growth['messages'],

        'monthly_chats_growth': monthly_growth['chats'],

        

        # Роли пользователей

        'students_count': user_roles['students_count'],

        'authors_count': user_roles['authors_count'],

        'admins_count': user_roles['admins_count'],

        

        # Уровни сложности

        'beginner_courses': difficulty_levels['beginner_courses'],

        'intermediate_courses': difficulty_levels['intermediate_courses'],

        'advanced_courses': difficulty_levels['advanced_courses'],

        

        # Проценты

        **percentages,

        

        # Данные для графиков

        'user_registrations': user_registrations[::-1],  # Reverse for chronological order

        'course_creations': course_creations[::-1],

        'months_labels': months_labels[::-1],

        'weekday_activity': weekday_activity,

        'weekday_labels': weekday_labels,

        'top_courses': top_courses,

        'programming_languages': programming_languages,

    })

    

    context = {

        'stats': stats,

        'days': days,

        'title': 'Детальная статистика',

    }

    return render(request, 'adminpanel/statistics.html', context)





# Пользователи CRUD (сохраняем существующие функции)

@admin_required

def user_list(request):

    """Список пользователей"""

    users = User.objects.all().order_by('-date_joined')

    context = {

        'users': users,

        'title': 'Управление пользователями',

    }

    return render(request, 'adminpanel/user_list.html', context)





@admin_required

def user_create(request):

    """Создание пользователя"""

    from .forms import UserForm

    if request.method == 'POST':

        form = UserForm(request.POST, request.FILES)

        if form.is_valid():

            user = form.save(commit=False)

            user.set_password(form.cleaned_data['password'])

            user.save()

            

            # Логируем создание пользователя

            from .middleware import ActivityLogger

            ActivityLogger.log_activity(

                user=request.user,

                action_type='create_user',

                request=request,

                obj=user,

                details={'created_username': user.username}

            )

            

            messages.success(request, f'Пользователь {user.username} создан.')

            return redirect('adminpanel:user_list')

    else:

        form = UserForm()

    

    context = {

        'form': form,

        'title': 'Создание пользователя',

    }

    return render(request, 'adminpanel/user_form.html', context)





@admin_required

def user_edit(request, user_id):

    """Редактирование пользователя"""

    from .forms import UserForm

    user = get_object_or_404(User, id=user_id)

    

    if request.method == 'POST':

        form = UserForm(request.POST, request.FILES, instance=user)

        if form.is_valid():

            updated_user = form.save(commit=False)

            if form.cleaned_data.get('password'):

                updated_user.set_password(form.cleaned_data['password'])

            updated_user.save()

            

            # Логируем обновление пользователя

            from .middleware import ActivityLogger

            ActivityLogger.log_activity(

                user=request.user,

                action_type='update_user',

                request=request,

                obj=user,

                details={'updated_fields': list(form.changed_data)}

            )

            

            messages.success(request, f'Пользователь {user.username} обновлен.')

            return redirect('adminpanel:user_list')

    else:

        form = UserForm(instance=user)

    

    context = {

        'form': form,

        'user': user,

        'title': 'Редактирование пользователя',

    }

    return render(request, 'adminpanel/user_form.html', context)





@admin_required

def user_delete(request, user_id):

    """Удаление пользователя"""

    user = get_object_or_404(User, id=user_id)

    

    if request.method == 'POST':

        username = user.username

        

        # Логируем удаление пользователя

        from .middleware import ActivityLogger

        ActivityLogger.log_activity(

            user=request.user,

            action_type='delete_user',

            request=request,

            obj=user,

            details={'deleted_username': username}

        )

        

        user.delete()

        messages.success(request, f'Пользователь {username} удален.')

        return redirect('adminpanel:user_list')

    

    context = {

        'user': user,

        'title': 'Удаление пользователя',

    }

    return render(request, 'adminpanel/user_delete.html', context)





# Курсы CRUD

@admin_required

def course_list(request):

    """Список курсов"""

    courses = Course.objects.select_related('instructor').prefetch_related(

        'enrollments', 'likes', 'reviews'

    ).order_by('-created_at')

    context = {

        'courses': courses,

        'title': 'Управление курсами',

    }

    return render(request, 'adminpanel/course_list.html', context)





@admin_required

def course_create(request):

    """Создание курса"""

    from .forms import CourseForm

    instructors = User.objects.filter(role='teacher').order_by('username')
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':

        form = CourseForm(request.POST, request.FILES)

        if form.is_valid():

            course = form.save()

            

            # Логируем создание курса

            from .middleware import ActivityLogger

            ActivityLogger.log_activity(

                user=request.user,

                action_type='create_course',

                request=request,

                obj=course

            )

            

            messages.success(request, f'Курс "{course.title}" создан.')

            return redirect('adminpanel:course_list')

    else:

        form = CourseForm()

    

    context = {

        'form': form,

        'instructors': instructors,

        'categories': categories,

        'title': 'Создание курса',

    }

    return render(request, 'adminpanel/course_form.html', context)





@admin_required

def course_edit(request, course_id):

    """Редактирование курса"""

    from .forms import CourseForm

    course = get_object_or_404(Course, id=course_id)

    

    if request.method == 'POST':

        form = CourseForm(request.POST, request.FILES, instance=course)

        if form.is_valid():

            course = form.save()

            

            # Логируем обновление курса

            from .middleware import ActivityLogger

            ActivityLogger.log_activity(

                user=request.user,

                action_type='update_course',

                request=request,

                obj=course,

                details={'updated_fields': list(form.changed_data)}

            )

            

            messages.success(request, f'Курс "{course.title}" обновлен.')

            return redirect('adminpanel:course_list')

    else:

        form = CourseForm(instance=course)

    

    context = {

        'form': form,

        'course': course,

        'instructors': instructors,

        'categories': categories,

        'title': 'Редактирование курса',

    }

    return render(request, 'adminpanel/course_form.html', context)





@admin_required

def course_delete(request, course_id):

    """Удаление курса"""

    course = get_object_or_404(Course, id=course_id)

    

    if request.method == 'POST':

        title = course.title

        

        # Логируем удаление курса

        from .middleware import ActivityLogger

        ActivityLogger.log_activity(

            user=request.user,

            action_type='delete_course',

            request=request,

            obj=course,

            details={'deleted_title': title}

        )

        

        course.delete()

        messages.success(request, f'Курс "{title}" удален.')

        return redirect('adminpanel:course_list')

    

    context = {

        'course': course,

        'title': 'Удаление курса',

    }

    return render(request, 'adminpanel/course_delete.html', context)





# Записи на курсы



# Бэкапы системы

@admin_required

def create_backup(request):

    """Создание полного бэкапа системы"""

    from .backup_utils import SystemBackup

    

    if request.method == 'POST':

        try:

            backup_system = SystemBackup()

            result = backup_system.create_full_backup(user=request.user)

            

            if result['success']:

                messages.success(

                    request, 

                    f'Бэкап "{result["filename"]}" успешно создан. '

                    f'Размер: {result["size"] / 1024 / 1024:.2f} MB'

                )

            else:

                messages.error(request, 'Ошибка при создании бэкапа')

                

        except Exception as e:

            messages.error(request, f'Ошибка при создании бэкапа: {str(e)}')

        

        return redirect('adminpanel:backup_logs')

    

    context = {

        'title': 'Создание бэкапа',

    }

    return render(request, 'adminpanel/create_backup.html', context)





@admin_required

def backup_logs(request):

    """Просмотр логов бэкапов"""

    from .backup_utils import SystemBackup

    

    # Получаем логи бэкапов из базы

    backup_logs = BackupLog.objects.select_related('created_by').order_by('-started_at')

    

    # Получаем список файлов бэкапов

    backup_system = SystemBackup()

    backup_files = backup_system.list_backups()

    backup_info = backup_system.get_backup_info()

    

    # Пагинация логов

    paginator = Paginator(backup_logs, 20)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    

    context = {

        'page_obj': page_obj,

        'backup_files': backup_files,

        'backup_info': backup_info,

        'title': 'Логи бэкапов',

    }

    return render(request, 'adminpanel/backup_logs.html', context)





@admin_required

def download_backup(request, filename):

    """Скачивание файла бэкапа"""

    from .backup_utils import SystemBackup

    

    try:

        backup_system = SystemBackup()

        backup_path = os.path.join(backup_system.backup_dir, filename)

        

        if os.path.exists(backup_path) and filename.endswith('.zip'):

            # Логируем скачивание

            from .middleware import ActivityLogger

            ActivityLogger.log_system_event(

                level='INFO',

                message=f"[BACKUP] Downloaded backup: {filename}",

                module='backup_system',

                function='download_backup',

                user=request.user,

                details={'filename': filename}

            )

            

            with open(backup_path, 'rb') as f:

                response = HttpResponse(f.read(), content_type='application/zip')

                response['Content-Disposition'] = f'attachment; filename="{filename}"'

                return response

        else:

            messages.error(request, 'Файл бэкапа не найден')

            

    except Exception as e:

        messages.error(request, f'Ошибка при скачивании бэкапа: {str(e)}')

    

    return redirect('adminpanel:backup_logs')





@admin_required

def delete_backup(request, filename):

    """Удаление бэкапа"""

    from .backup_utils import SystemBackup

    

    if request.method == 'POST':

        try:

            backup_system = SystemBackup()

            success = backup_system.delete_backup(filename, user=request.user)

            

            if success:

                messages.success(request, f'Бэкап "{filename}" удален')

            else:

                messages.error(request, 'Не удалось удалить бэкап')

                

        except Exception as e:

            messages.error(request, f'Ошибка при удалении бэкапа: {str(e)}')

    

    return redirect('adminpanel:backup_logs')





@admin_required

def restore_backup(request, filename):

    """Восстановление из бэкапа"""

    from .backup_utils import SystemBackup

    

    if request.method == 'POST':

        try:

            backup_system = SystemBackup()

            backup_path = os.path.join(backup_system.backup_dir, filename)

            

            result = backup_system.restore_backup(backup_path, user=request.user)

            

            if result['success']:

                messages.success(request, 'Система успешно восстановлена из бэкапа')

            else:

                messages.error(request, 'Ошибка при восстановлении системы')

                

        except Exception as e:

            messages.error(request, f'Ошибка при восстановлении: {str(e)}')

    

    return redirect('adminpanel:backup_logs')

@admin_required

def enrollment_list(request):

    """Список записей на курсы"""

    enrollments = CourseEnrollment.objects.select_related('user', 'course').order_by('-enrolled_at')

    context = {

        'enrollments': enrollments,

        'title': 'Записи на курсы',

    }

    return render(request, 'adminpanel/enrollment_list.html', context)





@admin_required

def enrollment_delete(request, enrollment_id):

    """Удаление записи"""

    enrollment = get_object_or_404(CourseEnrollment, id=enrollment_id)

    

    if request.method == 'POST':

        course_title = enrollment.course.title

        student_username = enrollment.user.username

        enrollment.delete()

        messages.success(request, f'Запись {student_username} на курс "{course_title}" удалена.')

        return redirect('adminpanel:enrollment_list')

    

    context = {

        'enrollment': enrollment,

        'title': 'Удаление записи',

    }

    return render(request, 'adminpanel/enrollment_delete.html', context)





# Лайки

@admin_required

def like_list(request):

    """Список лайков"""

    likes = CourseLike.objects.select_related('user', 'course').order_by('-created_at')

    context = {

        'likes': likes,

        'title': 'Лайки курсов',

    }

    return render(request, 'adminpanel/like_list.html', context)





@admin_required

def like_delete(request, like_id):

    """Удаление лайка"""

    like = get_object_or_404(CourseLike, id=like_id)

    

    if request.method == 'POST':

        course_title = like.course.title

        user_username = like.user.username

        like.delete()

        messages.success(request, f'Лайк {user_username} на курс "{course_title}" удален.')

        return redirect('adminpanel:like_list')

    

    context = {

        'like': like,

        'title': 'Удаление лайка',

    }

    return render(request, 'adminpanel/like_delete.html', context)





# Отзывы

@admin_required

def review_list(request):

    """Список отзывов"""

    reviews = CourseReview.objects.select_related('user', 'course').order_by('-created_at')

    context = {

        'reviews': reviews,

        'title': 'Отзывы курсов',

    }

    return render(request, 'adminpanel/review_list.html', context)





@admin_required

def review_delete(request, review_id):

    """Удаление отзыва"""

    review = get_object_or_404(CourseReview, id=review_id)

    

    if request.method == 'POST':

        course_title = review.course.title

        user_username = review.user.username

        review.delete()

        messages.success(request, f'Отзыв {user_username} на курс "{course_title}" удален.')

        return redirect('adminpanel:review_list')

    

    context = {

        'review': review,

        'title': 'Удаление отзыва',

    }

    return render(request, 'adminpanel/review_delete.html', context)

