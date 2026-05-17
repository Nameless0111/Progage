@echo off
setlocal EnableExtensions

set "START_DIR=%~dp0"
cd /d "%START_DIR%"

if not exist manage.py (
    set "MANAGE_FILE="
    for /f "delims=" %%F in ('dir /s /b manage.py 2^>nul') do (
        set "MANAGE_FILE=%%F"
        goto found_manage
    )
    echo Не удалось найти manage.py. Положите этот файл в папку проекта Progage.
    pause
    exit /b 1
)
set "MANAGE_FILE=%CD%\manage.py"

:found_manage
for %%I in ("%MANAGE_FILE%") do set "PROJECT_DIR=%%~dpI"
cd /d "%PROJECT_DIR%"

set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py -3"
if "%PY_CMD%"=="" (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)
if "%PY_CMD%"=="" (
    echo Python 3 не найден. Установите Python 3.12 или новее и запустите файл снова.
    pause
    exit /b 1
)

if not exist venv\Scripts\python.exe (
    echo Создание виртуального окружения...
    %PY_CMD% -m venv venv
    if errorlevel 1 (
        echo Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Не удалось активировать виртуальное окружение.
    pause
    exit /b 1
)

echo Установка зависимостей...
python -m pip install --upgrade pip
set "REQ_FILE=requirements.txt"
if exist requirements-local.txt set "REQ_FILE=requirements-local.txt"
if exist wheelhouse (
    pip install --no-index --find-links=wheelhouse -r "%REQ_FILE%"
) else (
    pip install -r "%REQ_FILE%"
)
if errorlevel 1 (
    echo Не удалось установить зависимости. Проверьте интернет или добавьте папку wheelhouse в пакет.
    pause
    exit /b 1
)

set "LOAD_ENV_LOCAL=0"
set "DJANGO_SETTINGS_MODULE=progage.settings"
set "SECRET_KEY=local-demo-secret-%RANDOM%-%RANDOM%-%RANDOM%"
set "DEBUG=True"
set "ALLOWED_HOSTS=localhost,127.0.0.1"
set "CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001"
set "DATABASE_URL=sqlite:///db.sqlite3"
set "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend"
set "RATE_LIMIT_ENABLED=False"

echo Подготовка базы данных...
python manage.py migrate
if errorlevel 1 (
    echo Не удалось применить миграции базы данных.
    pause
    exit /b 1
)

python manage.py ensure_demo_data --reset-passwords
python manage.py collectstatic --noinput >nul

set "PORT=8000"
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue) { exit 1 }"
if errorlevel 1 set "PORT=8001"

echo.
echo Progage запускается по адресу http://127.0.0.1:%PORT%/
echo Демо-аккаунты:
echo   admin   / Admin12345
echo   teacher / Teacher12345
echo   student / Student12345
echo.

start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:%PORT%/"
python manage.py runserver 127.0.0.1:%PORT%

pause
