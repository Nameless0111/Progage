# Развертывание сайта Progage на хостинге

## Подготовка файлов

### 1. Дамп базы данных
- Создайте дамп базы данных: `python manage.py dumpdata --indent=2 > dump.json`
- Очистите Unicode символы из базы данных при необходимости

### 2. Архив сайта
- Создайте архив с файлами проекта (без больших файлов и кэша)
- Исключите: `__pycache__`, `*.pyc`, `.git`, `venv`, `env`, `*.log`

## Развертывание на хостинге sweb

### 1. Создание кластера базы данных

В панели управления sweb:

1. **Перейдите в раздел "Базы данных"**
2. **Создайте кластер** с параметрами:
   - **CPU**: 1 ядро
   - **RAM**: 1 ГБ  
   - **Диск**: 10 ГБ NVMe
   - **Тип базы данных**: PostgreSQL 17

3. **Создайте базу данных**:
   - **Отображаемое имя**: Progage DB
   - **Пользователь**: задайте логин и пароль

### 2. Загрузка файлов

1. **Перейдите в "Файловый менеджер"**
2. **Загрузите архив с файлами сайта**
3. **Распакуйте архив** в корневую директорию сайта

### 3. Импорт базы данных

1. **Загрузите файл `dump.json`**
2. **Перейдите в "Базы данных"**
3. **Импортируйте базу из файла**

### 4. Настройка окружения

Создайте файл `.env.production`:

```bash
# База данных PostgreSQL
DB_NAME=progage_db
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=5432

# Django settings
SECRET_KEY=your_production_secret_key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=1

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 5. Установка зависимостей

Через SSH или терминал:

```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Применяем миграции
python manage.py migrate

# Собираем статические файлы
python manage.py collectstatic --noinput

# Создаем суперпользователя (если нужно)
python manage.py createsuperuser
```

### 6. Настройка веб-сервера

Создайте файл `passenger_wsgi.py`:

```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 7. Проверка работы

1. **Проверьте главную страницу**
2. **Проверьте админ-панель** по `/admin/`
3. **Проверьте функционал компилятора кода**

## Возможные проблемы

### Ошибка импорта базы данных
- Убедитесь, что тип БД PostgreSQL и версия совместимы
- Проверьте кодировку файла дампа (UTF-8)

### Ошибка модулей Python
- Проверьте `requirements.txt`
- Установите все зависимости: `pip install -r requirements.txt`

### Нет доступа к сайту
- Проверьте настройки `ALLOWED_HOSTS`
- Настройте DNS домена
- Проверьте логи ошибок

### Проблемы с компилятором кода
- Убедитесь, что установлены Node.js, Python, Java, gcc
- Проверьте права доступа к временным директориям

## Дополнительные настройки

1. **Настройте SSL** через панель управления
2. **Настройте резервное копирование** базы данных
3. **Настройте логирование** для мониторинга ошибок
4. **Оптимизируйте производительность** (кэширование, сжатие)

## Мониторинг

Регулярно проверяйте:
- Логи ошибок в панели управления
- Работоспособность компилятора кода
- Доступность сайта
- Использование ресурсов

## Важные файлы

- `.env.production` - настройки окружения
- `passenger_wsgi.py` - конфигурация WSGI
- `requirements.txt` - зависимости Python
- `dump.json` - дамп базы данных
