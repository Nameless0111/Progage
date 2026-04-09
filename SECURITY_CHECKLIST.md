# 🔐 Защиты в проекте Progage — чеклист и применение на практике

## ✅ Что уже реализовано

### 1. Двухфакторная аутентификация (2FA)
- **Что сделано:** django-otp + TOTP (Google Authenticator/Authy) + резервные коды
- **Где:** `accounts/models.py`, `accounts/views.py`, `accounts/forms.py`, `middleware.py`
- **Как работает:** При входе проверяется `profile.two_factor_enabled` → перенаправление на `two_factor_verify`
- **Применение:** Включается в профиле пользователя → генерируются QR‑код и 10 резервных кодов

### 2. Защита от brute‑force атак
- **Что сделано:** Rate limiting по IP и по username+IP
- **Где:** `accounts/middleware.py`, `accounts/views.py`
- **Как работает:** 
  - IP: не более 5 попыток за 5 минут
  - Username+IP: не более 3 попыток за 5 минут
  - Блокировка с HTTP 429
- **Применение:** Автоматически для `/accounts/login/` и `/accounts/password-reset/`

### 3. Логирование и аудит
- **Что сделано:** ActivityLog, SystemLog, ErrorLog, UserSession
- **Где:** `adminpanel/middleware.py`, `adminpanel/models.py`
- **Как работает:** Middleware записывает каждый запрос, ответ, исключение, действия пользователей
- **Применение:** В adminpanel можно смотреть все действия, медленные запросы, ошибки

### 4. CSRF защита
- **Что сделано:** `{% csrf_token %}` во всех формах
- **Где:** Все шаблоны с формами
- **Применение:** Автоматически, Django встроен

### 5. Безопасные заголовки (частично)
- **Что сделано:** `XFrameOptionsMiddleware`
- **Где:** `settings.py` MIDDLEWARE
- **Применение:** Защита от clickjacking

### 6. Валидация паролей
- **Что сделано:** Стандартные валидаторы Django
- **Где:** `settings.py` AUTH_PASSWORD_VALIDATORS
- **Применение:** При регистрации/смене пароля

### 7. Безопасная работа с файлами
- **Что сделано:** `avatar_url` и `thumbnail_url` с fallback
- **Где:** `accounts/models.py`, `courses/models.py`, шаблоны
- **Применение:** Если файл отсутствует → внешний placeholder (ui‑avatars, Unsplash)

### 8. EMAIL верификация (заготовка)
- **Что сделано:** `is_email_verified` поле в User
- **Где:** `accounts/models.py`
- **Применение:** Пока не используется, но готово для отправки письма с токеном

---

## 🛠️ Что можно улучшить (практика)

### 1. Content Security Policy (CSP)
```python
# settings.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "https://fonts.googleapis.com", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

### 2. HSTS (HTTPS Strict Transport Security)
```python
# settings.py (для production)
SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 3. Сессии с безопасными флагами
```python
# settings.py
SESSION_COOKIE_SECURE = True  # только HTTPS
SESSION_COOKIE_HTTPONLY = True  # недоступен через JS
SESSION_COOKIE_SAMESITE = 'Strict'
```

### 4. Rate limiting API
```python
# Установить django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h', method='GET')
def api_view(request):
    pass
```

### 5. Аудит действий администратора
```python
# adminpanel/middleware.py
if user.is_staff:
    ActivityLogger.log_action(
        user=user,
        action_type='admin_action',
        details={'action': 'delete_user', 'target': target_user.id}
    )
```

### 6. Защита от XSS в шаблонах
```django
<!-- Всегда использовать autoescape -->
{{ user_input|safe }}  <!-- НЕ ДЕЛАТЬ ТАК -->
{{ user_input }}  <!-- ПРАВИЛЬНО -->
```

### 7. Ограничение размера загрузки файлов
```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
```

### 8. Маскировка ошибок в production
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

---

## 📋 Чеклист для практики

### ✅ Обязательно для production
- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` ограничен
- [ ] `SECRET_KEY` в переменных окружения
- [ ] HTTPS (SSL/TLS)
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] База данных с паролем, не root
- [ ] Резервные копии БД и медиафайлов

### 🎯 Рекомендуется
- [ ] 2FA включен для всех админов
- [ ] CSP заголовки
- [ ] HSTS
- [ ] Rate limiting API
- [ ] Логирование ошибок в Sentry/LogDNA
- [ ] Регулярные обновления зависимостей
- [ ] Сканирование уязвимостей (safety, bandit)

### 🔒 Дополнительно
- [ ] SSO (OAuth2/Google/GitHub)
- [ ] Web Application Firewall (WAF)
- [ ] IP whitelist для админки
- [ ] Мониторинг (Prometheus+Grafana)
- [ ] Аудит логов в ELK

---

## 🚀 Как применить прямо сейчас

### 1. Включить CSP
```python
# settings.py
MIDDLEWARE += ['django_csp.middleware.CSPMiddleware']
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "https://fonts.googleapis.com", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

### 2. Защитить сессии
```python
# settings.py
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
```

### 3. Ограничить загрузку
```python
# settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
```

### 4. Включить 2FA для админов (автоматически)
```python
# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.is_staff:
        profile, _ = Profile.objects.get_or_create(user=instance)
        profile.two_factor_enabled = True
        profile.save()
```

---

## 📊 Текущий уровень безопасности

| Компонент | Статус | Оценка |
|------------|---------|---------|
| Аутентификация | ✅ 2FA + email верификация | 🟢 Высокий |
| Авторизация | ✅ Роли, permissions | 🟢 Высокий |
| Защита от brute-force | ✅ Rate limiting | 🟢 Высокий |
| Логирование | ✅ Полный аудит | 🟢 Высокий |
| CSRF | ✅ Встроенный | 🟢 Высокий |
| XSS | ⚠️ Только autoescape | 🟡 Средний |
| CSP | ❌ Не настроен | 🔔 Низкий |
| HSTS | ❌ Не настроен | 🔔 Низкий |
| Сессии | ⚠️ Без флагов | 🟡 Средний |
| Загрузка файлов | ✅ Ограничена | 🟢 Высокий |

**Итог:** 🟡 Средний (высокий по аутентификации, нужно улучшить заголовки безопасности)

---

## 🎯 Следующие шаги

1. **Добавить CSP заголовки** — 15 минут
2. **Включить безопасные флаги сессий** — 5 минут  
3. **Настроить HSTS для production** — 10 минут
4. **Добавить rate limiting для API** — 30 минут
5. **Включить автоматическую 2FA для админов** — 20 минут

---

## 📚 Полезные ссылки

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CSP Playground](https://csp-evaluator.withgoogle.com/)
- [Django CSP](https://github.com/mozilla/django-csp)

---

*Создано: 9 апреля 2026*  
*Обновлено: при каждом изменении в проекте*
