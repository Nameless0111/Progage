# Структура проекта Progage - Обновленная таблица

| № п/п | Название модуля | Описание модуля | Размер модуля | Кол-во строк | Категория |
|-------|----------------|----------------|--------------|--------------|-----------|
| 1 | manage.py | Главный файл управления Django проектом | 0.7 КБ | 23 | Backend |
| 2 | progage/settings.py | Основные настройки Django приложения | 10.1 КБ | 256 | Backend |
| 3 | progage/urls.py | Основной файл URL маршрутизации | 0.8 КБ | 19 | Backend |
| 4 | progage/wsgi.py | WSGI конфигурация для развертывания | 0.6 КБ | 17 | Backend |
| 5 | progage/asgi.py | ASGI конфигурация для WebSocket | 0.9 КБ | 22 | Backend |
| 6 | accounts/models.py | Модели пользователей и профилей | 3.3 КБ | 83 | Backend |
| 7 | courses/models.py | Модели курсов, уроков и записей | 5.6 КБ | 142 | Backend |
| 8 | chat/models.py | Модели чата и поддержки | 1.0 КБ | 25 | Backend |
| 9 | adminpanel/models.py | Модели логов и статистики | 10.1 КБ | 255 | Backend |
| 10 | accounts/views.py | Представления аутентификации и профилей | 14.5 КБ | 360 | Backend |
| 11 | courses/views.py | Представления курсов и уроков | 6.1 КБ | 150 | Backend |
| 12 | chat/views.py | Представления чата поддержки | 4.2 КБ | 105 | Backend |
| 13 | adminpanel/views.py | Представления административной панели | 56.3 КБ | 1378 | Backend |
| 14 | accounts/forms.py | Формы регистрации и профиля | 3.0 КБ | 78 | Backend |
| 15 | courses/forms.py | Формы курсов и уроков | 1.0 КБ | 25 | Backend |
| 16 | adminpanel/forms.py | Формы административной панели | 3.0 КБ | 77 | Backend |
| 17 | accounts/middleware.py | Middleware защиты от брутфорса | 2.6 КБ | 66 | Backend |
| 18 | adminpanel/middleware.py | Middleware логирования и мониторинга | 13.5 КБ | 348 | Backend |
| 19 | adminpanel/decorators.py | Декораторы доступа и прав | 0.6 КБ | 16 | Backend |
| 20 | adminpanel/backup_utils.py | Утилиты резервного копирования | 14.7 КБ | 377 | Backend |
| 21 | chat/consumers.py | WebSocket потребители чата | 4.6 КБ | 116 | Backend |
| 22 | chat/routing.py | WebSocket маршрутизация чата | 0.3 КБ | 7 | Backend |
| 23 | accounts/urls.py | URL маршрутизация аккаунтов | 0.9 КБ | 24 | Backend |
| 24 | courses/urls.py | URL маршрутизация курсов | 0.6 КБ | 14 | Backend |
| 25 | chat/urls.py | URL маршрутизация чата | 0.5 КБ | 13 | Backend |
| 26 | adminpanel/urls.py | URL маршрутизация админ-панели | 2.0 КБ | 52 | Backend |
| 27 | accounts/email_utils.py | Утилиты отправки email | 1.1 КБ | 29 | Backend |
| 28 | accounts/context_processors.py | Контекстные процессоры | 0.5 КБ | 12 | Backend |
| 29 | rate_limit_middleware.py | Middleware ограничения запросов | 1.1 КБ | 28 | Backend |
| 30 | requirements.txt | Зависимости Python | 0.5 КБ | 17 | Конфигурация |
| 31 | UNIFIED_PROJECT_CODE.md | Единый файл кода проекта | 126.4 КБ | 3247 | Документация |

## Итоговая статистика:

### По категориям:
- **Backend**: 29 файлов, 150.8 КБ, 3511 строк
- **Конфигурация**: 2 файла, 0.6 КБ, 44 строки  
- **Документация**: 1 файл, 126.4 КБ, 3247 строк

### По модулям:
- **accounts**: 9 файлов, 28.5 КБ, 694 строки
- **adminpanel**: 8 файлов, 100.5 КБ, 2503 строки
- **courses**: 6 файлов, 13.3 КБ, 331 строка
- **chat**: 6 файлов, 10.6 КБ, 266 строк
- **progage**: 5 файлов, 13.0 КБ, 317 строк
- **Основные файлы**: 2 файла, 1.2 КБ, 45 строк

### Ключевые характеристики:
- **Всего файлов**: 31
- **Общий размер**: 278.2 КБ
- **Всего строк**: 7157
- **Средний размер файла**: 9.0 КБ
- **Среднее количество строк**: 231

### Самые крупные файлы:
1. adminpanel/views.py - 56.3 КБ (1378 строк)
2. adminpanel/backup_utils.py - 14.7 КБ (377 строк)
3. adminpanel/middleware.py - 13.5 КБ (348 строк)
4. progage/settings.py - 10.1 КБ (256 строк)
5. adminpanel/models.py - 10.1 КБ (255 строк)
