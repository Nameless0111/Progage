"""
Global Rate Limiting Middleware for all requests
Protects against DDoS and excessive requests
"""
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time

class GlobalRateLimitMiddleware(MiddlewareMixin):
    """Глобальный rate limiting для защиты от DDoS"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        if not getattr(settings, 'RATE_LIMIT_ENABLED', True) or self.is_exempt_path(request.path):
            return self.get_response(request)

        client_ip = self.get_client_ip(request)
        global_limit = self.get_global_limit(request)
        window = getattr(settings, 'RATE_LIMIT_WINDOW_SECONDS', 60)
        
        # Глобальные лимиты
        if self.is_rate_limited_global(client_ip, global_limit, window):
            return HttpResponse(
                "Rate limit exceeded. Try again later.",
                status=429,
                headers={'Retry-After': str(window)}
            )
        
        # Специфичные лимиты для API
        if self.is_api_path(request.path) and self.is_rate_limited_api(client_ip, window):
            return HttpResponse(
                "API rate limit exceeded.",
                status=429,
                headers={'Retry-After': str(window)}
            )
        
        response = self.get_response(request)
        
        # Добавляем rate limit headers
        response['X-RateLimit-Limit'] = str(global_limit)
        response['X-RateLimit-Remaining'] = str(max(0, global_limit - self.get_request_count(client_ip)))
        response['X-RateLimit-Reset'] = str(int(time.time()) + window)
        
        return response

    def is_exempt_path(self, path):
        """Не лимитируем статические и пользовательские файлы."""
        return path.startswith('/static/') or path.startswith('/media/')

    def is_api_path(self, path):
        """API в проекте есть как на /api/, так и внутри /courses/api/."""
        return path.startswith('/api/') or '/api/' in path

    def get_global_limit(self, request):
        if getattr(request, 'user', None) and request.user.is_authenticated:
            return getattr(settings, 'RATE_LIMIT_AUTHENTICATED_REQUESTS', 1200)
        return getattr(settings, 'RATE_LIMIT_GLOBAL_REQUESTS', 600)
    
    def get_client_ip(self, request):
        """Получаем реальный IP клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited_global(self, ip, limit, window):
        """Глобальный лимит запросов на IP."""
        cache_key = f'rate_limit_global_{ip}'
        count = cache.get(cache_key, 0)
        
        if count >= limit:
            return True
        
        # Увеличиваем счетчик
        cache.set(cache_key, count + 1, window)
        return False
    
    def is_rate_limited_api(self, ip, window):
        """Лимит для API-запросов на IP."""
        cache_key = f'rate_limit_api_{ip}'
        count = cache.get(cache_key, 0)
        limit = getattr(settings, 'RATE_LIMIT_API_REQUESTS', 180)
        
        if count >= limit:
            return True
        
        cache.set(cache_key, count + 1, window)
        return False
    
    def get_request_count(self, ip):
        """Получаем текущее количество запросов"""
        cache_key = f'rate_limit_global_{ip}'
        return cache.get(cache_key, 0)
