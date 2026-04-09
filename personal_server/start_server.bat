
@echo off
echo Запуск Progage сервера...
cd /d "C:\Progage"

REM Запуск PostgreSQL
docker run -d --name progage_db ^
    -e POSTGRES_DB=progage_db ^
    -e POSTGRES_USER=progage_user ^
    -e POSTGRES_PASSWORD=1111 ^
    -p 5432:5432 ^
    -v postgres_data:/var/lib/postgresql/data ^
    postgres:15

REM Ожидание запуска PostgreSQL
timeout /t 30

REM Запуск Redis
docker run -d --name progage_redis -p 6379:6379 redis:7-alpine

REM Запуск Django
call venv\Scripts\activate
set DJANGO_SETTINGS_MODULE=progage.settings
set DATABASE_URL=postgresql://progage_user:1111@localhost:5432/progage_db

REM Сбор статики
python manage.py collectstatic --noinput

REM Запуск Gunicorn
start /B gunicorn --workers 3 --bind 0.0.0.0:8000 progage.wsgi:application

echo Сервер запущен на http://%IP%
pause
