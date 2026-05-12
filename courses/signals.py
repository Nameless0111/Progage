from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender='courses.Lesson')
def lesson_created_notification(sender, instance, created, **kwargs):
    """Отправка уведомлений при создании нового урока"""
    if not created:
        return  # Только для новых уроков
    
    try:
        from accounts.models import Notification, UserNotifications
        
        # Получаем всех студентов, записанных на курс
        enrolled_users = User.objects.filter(
            courseenrollment__course=instance.course,
            courseenrollment__is_active=True
        ).distinct()
        
        for user in enrolled_users:
            # Проверяем настройки уведомлений пользователя
            try:
                notifications_settings = user.notification_settings
                if notifications_settings.new_lessons:
                    # Создаем уведомление
                    Notification.objects.create(
                        user=user,
                        notification_type='new_lesson',
                        title=f'Новый урок в курсе "{instance.course.title}"',
                        message=f'В курсе "{instance.course.title}" появился новый урок: "{instance.title}"',
                        course=instance.course,
                        lesson=instance
                    )
            except UserNotifications.DoesNotExist:
                # Если у пользователя нет настроек, создаем их по умолчанию
                UserNotifications.objects.create(user=user)
                # И создаем уведомление
                Notification.objects.create(
                    user=user,
                    notification_type='new_lesson',
                    title=f'Новый урок в курсе "{instance.course.title}"',
                    message=f'В курсе "{instance.course.title}" появился новый урок: "{instance.title}"',
                    course=instance.course,
                    lesson=instance
                )
                
    except Exception as e:
        # Логируем ошибку, но не прерываем процесс
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending lesson notification: {e}")
