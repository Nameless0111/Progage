@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Progage local launcher. Keep this file ASCII-only for Windows cmd.
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "BAT_DIR=%~dp0"
set "PROJECT_DIR="

if exist "%BAT_DIR%manage.py" set "PROJECT_DIR=%BAT_DIR%"
if not defined PROJECT_DIR if exist "%BAT_DIR%Progage\manage.py" set "PROJECT_DIR=%BAT_DIR%Progage\"
if not defined PROJECT_DIR if exist "%CD%\manage.py" set "PROJECT_DIR=%CD%\"
if not defined PROJECT_DIR if exist "%CD%\Progage\manage.py" set "PROJECT_DIR=%CD%\Progage\"
if not defined PROJECT_DIR if exist "%~d0\Progage\manage.py" set "PROJECT_DIR=%~d0\Progage\"

if not defined PROJECT_DIR (
    echo Progage launcher error.
    echo manage.py was not found.
    echo Put RUN_PROGAGE.bat into the Progage project folder and run it again.
    pause
    exit /b 1
)

pushd "%PROJECT_DIR%" >nul
if errorlevel 1 (
    echo Progage launcher error.
    echo Cannot enter project folder: "%PROJECT_DIR%"
    pause
    exit /b 1
)

if not exist "manage.py" (
    echo Progage launcher error.
    echo manage.py is missing in: "%CD%"
    pause
    exit /b 1
)

set "PYTHONPATH=%CD%;%PYTHONPATH%"
set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py -3"

if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
    echo Python 3 was not found.
    echo Install Python 3.12 or newer and run this file again.
    pause
    exit /b 1
)

if /i "%~1"=="--check" (
    echo Launcher check OK.
    echo Project folder: "%CD%"
    echo Python command: %PY_CMD%
    popd >nul
    exit /b 0
)

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY_CMD% -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip.
    pause
    exit /b 1
)

set "REQ_FILE=requirements.txt"
if exist "requirements-local.txt" set "REQ_FILE=requirements-local.txt"

if exist "wheelhouse\" (
    pip install --no-index --find-links=wheelhouse -r "%REQ_FILE%"
) else (
    pip install -r "%REQ_FILE%"
)
if errorlevel 1 (
    echo Failed to install dependencies.
    echo Check internet connection or add the wheelhouse folder to the package.
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

echo Preparing database...
python manage.py migrate
if errorlevel 1 (
    echo Failed to apply database migrations.
    pause
    exit /b 1
)

python manage.py ensure_demo_data --reset-passwords
if errorlevel 1 (
    echo Failed to create demo data.
    pause
    exit /b 1
)

python manage.py collectstatic --noinput >nul

set "PORT=8000"
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>nul
if not errorlevel 1 set "PORT=8001"

echo.
echo Progage is starting at http://127.0.0.1:%PORT%/
echo Demo accounts:
echo   admin   / Admin12345
echo   teacher / Teacher12345
echo   student / Student12345
echo.

start "" "http://127.0.0.1:%PORT%/"
python manage.py runserver 127.0.0.1:%PORT%

popd >nul
pause
