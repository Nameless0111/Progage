@echo off
echo 🚀 Запуск Django сервера...
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
echo ✅ Django сервер запущен!
echo 📍 Локальный доступ: http://localhost:8000
pause
