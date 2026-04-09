"""
Global Rate Limiting Middleware for all requests
Protects against DDoS and excessive requests
"""
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time

class GlobalRateLimitMiddleware(MiddlewareMixin):
    """Глобальный rate limiting для защиты от DDoS"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        client_ip = self.get_client_ip(request)
        
        # Глобальные лимиты
        if self.is_rate_limited_global(client_ip):
            return HttpResponse(
                "Rate limit exceeded. Try again later.",
                status=429,
                headers={'Retry-After': '60'}
            )
        
        # Специфичные лимиты для API
        if request.path.startswith('/api/') and self.is_rate_limited_api(client_ip):
            return HttpResponse(
                "API rate limit exceeded.",
                status=429,
                headers={'Retry-After': '30'}
            )
        
        response = self.get_response(request)
        
        # Добавляем rate limit headers
        response['X-RateLimit-Limit'] = '100'
        response['X-RateLimit-Remaining'] = str(max(0, 100 - self.get_request_count(client_ip)))
        response['X-RateLimit-Reset'] = str(int(time.time()) + 60)
        
        return response
    
    def get_client_ip(self, request):
        """Получаем реальный IP клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited_global(self, ip):
        """Глобальный лимит: 100 запросов в минуту на IP"""
        cache_key = f'rate_limit_global_{ip}'
        count = cache.get(cache_key, 0)
        
        if count >= 100:
            return True
        
        # Увеличиваем счетчик
        cache.set(cache_key, count + 1, 60)  # 60 секунд
        return False
    
    def is_rate_limited_api(self, ip):
        """Лимит для API: 30 запросов в минуту на IP"""
        cache_key = f'rate_limit_api_{ip}'
        count = cache.get(cache_key, 0)
        
        if count >= 30:
            return True
        
        cache.set(cache_key, count + 1, 60)
        return False
    
    def get_request_count(self, ip):
        """Получаем текущее количество запросов"""
        cache_key = f'rate_limit_global_{ip}'
        return cache.get(cache_key, 0)
