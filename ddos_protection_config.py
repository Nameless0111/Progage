"""
DDoS Protection Configuration
Настраивает защиту от DDoS атак на разных уровнях
"""
import os
from django.conf import settings

# Глобальные лимиты защиты
DDOS_PROTECTION = {
    # Базовые лимиты
    'GLOBAL_REQUESTS_PER_MINUTE': 100,
    'GLOBAL_REQUESTS_PER_HOUR': 1000,
    'GLOBAL_REQUESTS_PER_DAY': 10000,
    
    # API лимиты (строже)
    'API_REQUESTS_PER_MINUTE': 30,
    'API_REQUESTS_PER_HOUR': 300,
    'API_REQUESTS_PER_DAY': 3000,
    
    # Лимиты для аутентификации
    'AUTH_REQUESTS_PER_MINUTE': 10,
    'AUTH_REQUESTS_PER_HOUR': 50,
    
    # Лимиты для форм
    'FORM_REQUESTS_PER_MINUTE': 20,
    'FORM_REQUESTS_PER_HOUR': 200,
    
    # Размер блокировки (в секундах)
    'BLOCK_DURATION': {
        'MINUTE': 60,
        'HOUR': 3600,
        'DAY': 86400,
        'PERMANENT': 604800  # 7 дней
    },
    
    # Белые IP адреса (не блокируются)
    'WHITELIST_IPS': [
        '127.0.0.1',
        '::1',
        'localhost',
    ],
    
    # Пути с особыми лимитами
    'SPECIAL_PATHS': {
        '/api/': 'API_REQUESTS_PER_MINUTE',
        '/accounts/login/': 'AUTH_REQUESTS_PER_MINUTE',
        '/accounts/register/': 'AUTH_REQUESTS_PER_MINUTE',
        '/accounts/password-reset/': 'AUTH_REQUESTS_PER_MINUTE',
        '/admin/': 'AUTH_REQUESTS_PER_MINUTE',
    },
    
    # Размеры запросов
    'MAX_REQUEST_SIZE': 10 * 1024 * 1024,  # 10MB
    'MAX_UPLOAD_SIZE': 50 * 1024 * 1024,   # 50MB
    
    # Включение/выключение защиты
    'ENABLED': True,
    'LOGGING': True,
    'STRICT_MODE': False,  # Блокировать при превышении любого лимита
}

# Настройки кэша для rate limiting
RATE_LIMIT_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 86400,  # 24 часа
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Заголовки безопасности для защиты от атак
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
}

# Мониторинг и алерты
MONITORING = {
    'ENABLED': True,
    'ALERT_THRESHOLD': 80,  # % от лимита для алерта
    'LOG_FILE': 'ddos_protection.log',
    'EMAIL_ALERTS': True,
    'WEBHOOK_URL': None,  # URL для уведомлений
}

def get_ddos_config():
    """Получить конфигурацию DDoS защиты"""
    return DDOS_PROTECTION

def is_whitelisted(ip):
    """Проверить IP в белом списке"""
    return ip in DDOS_PROTECTION['WHITELIST_IPS']

def get_rate_limit_for_path(path):
    """Получить лимиты для конкретного пути"""
    for pattern, limit_key in DDOS_PROTECTION['SPECIAL_PATHS'].items():
        if path.startswith(pattern):
            return DDOS_PROTECTION[limit_key]
    return DDOS_PROTECTION['GLOBAL_REQUESTS_PER_MINUTE']

def get_security_headers():
    """Получить заголовки безопасности"""
    return SECURITY_HEADERS

if __name__ == '__main__':
    # Тест конфигурации
    print("DDoS Protection Configuration:")
    print(f"Global limit: {DDOS_PROTECTION['GLOBAL_REQUESTS_PER_MINUTE']} requests/min")
    print(f"API limit: {DDOS_PROTECTION['API_REQUESTS_PER_MINUTE']} requests/min")
    print(f"Auth limit: {DDOS_PROTECTION['AUTH_REQUESTS_PER_MINUTE']} requests/min")
    print(f"Whitelisted IPs: {DDOS_PROTECTION['WHITELIST_IPS']}")
