# Progage

Progage - образовательная платформа на Django для курсов, уроков, тестов, практических заданий, чата поддержки и административной панели.

## Локальный запуск через Docker

Этот способ подходит для Windows, Linux и macOS. Нужен только Docker Desktop или Docker Engine с Docker Compose.

```bash
git clone <repository-url>
cd Progage
docker compose up --build
```

После запуска сайт будет доступен по адресу:

```text
http://localhost:8000
```

Миграции применяются автоматически при старте контейнера. База данных PostgreSQL и Redis запускаются отдельными контейнерами.

Создание администратора:

```bash
docker compose exec web python manage.py createsuperuser
```

Остановка:

```bash
docker compose down
```

Полная очистка локальной Docker-базы:

```bash
docker compose down -v
```

## Локальный запуск без Docker

Для ручного запуска нужен Python 3.11, PostgreSQL и Redis.

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

На Windows проект читает настройки из `.env.local`, если файл существует. Если после обновления проекта появляется ошибка импорта зависимости, выполните:

```bash
pip install -r requirements.txt
```

## Production на Ubuntu/VPS

Основной сценарий деплоя:

```bash
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart progage
```

Для production укажите в `.env.local` или переменных окружения:

```text
DEBUG=False
SECRET_KEY=<strong-secret>
ALLOWED_HOSTS=example.com,www.example.com,<server-ip>
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DATABASE_URL=postgresql://user:password@localhost:5432/progage_db
REDIS_URL=redis://localhost:6379/0
BACKUP_ROOT=/var/backups/progage
LOG_DIR=/var/log/progage
```

## Структура проекта

```text
accounts/      Пользователи, роли, профиль, 2FA, уведомления
adminpanel/    Внутренняя админ-панель, логи, бэкапы
chat/          Чат поддержки
courses/       Курсы, уроки, тесты, практические задания
progage/       Настройки, URL, WSGI/ASGI
templates/     HTML-шаблоны
static/        CSS и статические файлы
media/         Пользовательские файлы
backups/       Локальные архивы бэкапов
```

## Проверка проекта

```bash
python manage.py check
python manage.py showmigrations
```
