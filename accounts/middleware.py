from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
import time

class BruteForceProtectionMiddleware(MiddlewareMixin):
    """Защита от brute-force атак с rate limiting"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Применяем только к формам входа и восстановления пароля
        if request.path in ['/accounts/login/', '/accounts/password-reset/']:
            client_ip = self.get_client_ip(request)
            username = request.POST.get('username', '') if request.method == 'POST' else ''
            
            if self.is_blocked(client_ip, username):
                return HttpResponse(
                    "Слишком много попыток. Попробуйте через 5 минут.",
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
        # Проверяем блокировку по IP и по username+IP
        ip_key = f'login_attempts_ip_{ip}'
        user_key = f'login_attempts_user_{username}_{ip}' if username else None
        
        ip_attempts = cache.get(ip_key, 0)
        user_attempts = cache.get(user_key, 0) if user_key else 0
        
        # Блокировка если больше 5 попыток за 5 минут
        return ip_attempts >= 5 or user_attempts >= 3
    
    def record_attempt(self, ip, username):
        # Записываем попытку с TTL 5 минут
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


def get_unread_notifications_count(request):
    """Получает количество непрочитанных уведомлений для пользователя"""
    if not hasattr(request, '_unread_notifications_count'):
        if request.user.is_authenticated:
            try:
                from accounts.models import Notification
                count = Notification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count()
                request._unread_notifications_count = count
            except:
                request._unread_notifications_count = 0
        else:
            request._unread_notifications_count = 0
    
    return request._unread_notifications_count


class NotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Добавляем количество непрочитанных уведомлений в request
        request.unread_notifications_count = SimpleLazyObject(
            lambda: get_unread_notifications_count(request)
        )
        
        response = self.get_response(request)
        return response
