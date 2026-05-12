# Progage - Образовательная платформа

Progage - это современная образовательная платформа для создания и прохождения курсов.

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- Django 4.2+
- Node.js (для фронтенда)
- PostgreSQL или SQLite

### Установка
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd progage

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Для Windows
# или
venv\Scripts\activate  # Для Windows

# Установите зависимости
pip install -r requirements.txt

# Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env с вашими настройками

# Выполните миграции
python manage.py migrate

# Создайте суперпользователя
python manage.py createsuperuser

# Запустите сервер
python manage.py runserver
```

## 📁 Структура проекта

```
progage/
├── accounts/          # Пользователи и аутентификация
├── adminpanel/         # Админ-панель
├── courses/            # Курсы и уроки
├── progage/             # Основное приложение
├── chat/                # Чат и поддержка
├── templates/           # HTML шаблоны
├── static/              # Статические файлы
├── media/               # Медиафайлы пользователей
└── backups/             # Бэкапы системы
```

## 🔧 Разработка

### Основные команды
```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск тестов
python manage.py test

# Сбор статики
python manage.py collectstatic

# Запуск сервера разработки
python manage.py runserver
```

## 📚 Документация

Подробная документация находится в директории `docs/`.

## 🤝 Поддержка

Если у вас есть вопросы или проблемы, создайте issue в репозитории.
