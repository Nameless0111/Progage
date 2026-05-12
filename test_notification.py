import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from accounts.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

# Создадим тестовое уведомление
user = User.objects.first()
if user:
    Notification.objects.create(
        user=user,
        notification_type='system',
        title='Системное уведомление',
        message='Тестовое уведомление для проверки работы системы'
    )
    print('Test notification created')
else:
    print('No users found')
