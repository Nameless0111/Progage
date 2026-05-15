from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
import time

class BruteForceProtectionMiddleware(MiddlewareMixin):
    """Мягкое ограничение для восстановления пароля.

    Логин считает только неудачные попытки внутри view. Если middleware тоже
    записывает каждый POST, пользователь получает блокировку после пары ошибок.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        if request.path == '/accounts/password-reset/' and request.method == 'POST':
            client_ip = self.get_client_ip(request)
            
            if self.is_blocked(client_ip):
                return HttpResponse(
                    "Слишком много запросов на восстановление пароля. Попробуйте через 10 минут.",
                    status=429
                )
            
            self.record_attempt(client_ip)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_blocked(self, ip):
        attempts = cache.get(f'password_reset_attempts_ip_{ip}', 0)
        return attempts >= 10

    def record_attempt(self, ip):
        ip_key = f'password_reset_attempts_ip_{ip}'
        if cache.get(ip_key) is None:
            cache.set(ip_key, 1, 600)
        else:
            cache.incr(ip_key)


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
