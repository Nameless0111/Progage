# 📦 Руководство по использованию бэкапов Progage

## 🎯 Что такое бэкапы?

Бэкап - это полная копия вашей системы, включающая:
- 🗄️ **База данных** (все пользователи, курсы, уроки, настройки)
- 📁 **Медиафайлы** (аватары, изображения курсов, прикрепленные файлы)
- ⚙️ **Конфигурация** (settings.py, urls.py, requirements.txt)
- 📝 **Логи системы** (для отладки)
- 📊 **Метаданные** (статистика на момент создания)

---

## 🚀 Как создать бэкап

### 1. Через админ-панель:
1. Зайдите в **Админ-панель** → **Логи бэкапов**
2. Нажмите кнопку **"Создать бэкап"**
3. Дождитесь завершения процесса
4. Бэкап появится в списке файлов

### 2. Автоматическое создание:
```python
from adminpanel.backup_utils import SystemBackup

backup_system = SystemBackup()
backup_system.create_full_backup(user=request.user)
```

---

## 📥 Как скачать бэкап

### 1. Через админ-панель:
1. В **Логах бэкапов** найдите нужный файл
2. Нажмите кнопку **⬇** (скачать)
3. Сохраните ZIP-файл на компьютер

### 2. Что внутри ZIP-архива:
```
full_backup_20260512_135555.zip/
├── database/
│   └── database_dump_20260512_135555.sql    # Дамп базы данных
├── media/                                      # Все медиафайлы
│   ├── avatars/
│   ├── course_thumbnails/
│   └── lesson_attachments/
├── config/                                     # Конфигурационные файлы
│   ├── progage/settings.py
│   ├── progage/urls.py
│   ├── requirements.txt
│   └── .env
├── logs/                                       # Логи системы
│   └── debug.log
└── metadata.json                               # Метаданные бэкапа
```

---

## 🔄 Как восстановить из бэкапа

### ⚠️ ВАЖНО: Восстановление удаляет текущие данные!

### 1. Подготовка:
```bash
# 1. Остановите сервер Django
python manage.py runserver  # Ctrl+C

# 2. Сделайте текущий бэкап (на всякий случай)
python manage.py shell
>>> from adminpanel.backup_utils import SystemBackup
>>> SystemBackup().create_full_backup()
```

### 2. Восстановление базы данных:
```bash
# 1. Распакуйте ZIP-архив
unzip full_backup_20260512_135555.zip

# 2. Удалите текущую базу данных
rm db.sqlite3

# 3. Восстановите из дампа
sqlite3 db.sqlite3 < database/database_dump_20260512_135555.sql
```

### 3. Восстановление медиафайлов:
```bash
# 1. Сохраните текущие медиафайлы (если нужно)
mv media media_backup

# 2. Скопируйте медиафайлы из бэкапа
cp -r backup/media/ ./
```

### 4. Восстановление конфигурации:
```bash
# 1. Резервная копия текущих настроек
cp progage/settings.py progage/settings.py.backup
cp .env .env.backup

# 2. Восстановление из бэкапа
cp backup/config/progage/settings.py progage/settings.py
cp backup/config/.env .
```

### 5. Запуск системы:
```bash
# 1. Установка зависимостей
pip install -r backup/config/requirements.txt

# 2. Миграции (на случай изменений)
python manage.py migrate

# 3. Создание суперпользователя (если нужно)
python manage.py createsuperuser

# 4. Запуск сервера
python manage.py runserver
```

---

## 🛠️ Автоматическое восстановление (скрипт)

### Создайте скрипт `restore_backup.py`:
```python
#!/usr/bin/env python3
import os
import sys
import shutil
import sqlite3
import subprocess
from pathlib import Path

def restore_backup(backup_path):
    """Полное восстановление из бэкапа"""
    
    print(f"🔄 Восстановление из: {backup_path}")
    
    # 1. Распаковка
    extract_dir = Path("temp_restore")
    shutil.unpack_archive(backup_path, extract_dir)
    
    # 2. Восстановление базы данных
    db_file = "db.sqlite3"
    if os.path.exists(db_file):
        os.remove(db_file)
    
    sql_dump = extract_dir / "database" / "database_dump_*.sql"
    conn = sqlite3.connect(db_file)
    with open(sql_dump, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.close()
    
    # 3. Восстановление медиафайлов
    if os.path.exists("media"):
        shutil.move("media", "media_backup")
    shutil.copytree(extract_dir / "media", "media")
    
    # 4. Восстановление конфигурации
    config_files = [
        ("progage/settings.py", "progage/settings.py"),
        (".env", ".env"),
        ("requirements.txt", "requirements.txt")
    ]
    
    for src, dst in config_files:
        src_path = extract_dir / "config" / src
        if src_path.exists():
            shutil.copy2(src_path, dst)
    
    # 5. Очистка
    shutil.rmtree(extract_dir)
    
    print("✅ Восстановление завершено!")
    print("🚀 Перезапустите сервер: python manage.py runserver")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python restore_backup.py <backup_file.zip>")
        sys.exit(1)
    
    restore_backup(sys.argv[1])
```

### Использование:
```bash
python restore_backup.py full_backup_20260512_135555.zip
```

---

## 📅 Регулярность бэкапов

### Рекомендуемый график:
- 📊 **Ежедневные** - для активных систем
- 🗓️ **Еженедельные** - для среднезагруженных
- 📆 **Ежемесячные** - для тестовых систем

### Автоматизация через cron:
```bash
# Ежедневный бэкап в 2:00 ночи
0 2 * * * /path/to/venv/bin/python /path/to/manage.py shell -c "from adminpanel.backup_utils import SystemBackup; SystemBackup().create_full_backup()"

# Еженедельное удаление старых бэкапов (оставлять последние 7)
0 3 * * 0 find /path/to/backups -name "*.zip" -mtime +7 -delete
```

---

## 🔍 Проверка бэкапа

### Проверка целостности:
```python
import zipfile
import json

def check_backup_integrity(backup_path):
    """Проверка целостности бэкапа"""
    try:
        with zipfile.ZipFile(backup_path, 'r') as zip_file:
            # Проверка метаданных
            metadata = json.loads(zip_file.read('metadata.json'))
            print(f"📅 Дата создания: {metadata['created_at']}")
            print(f"👥 Пользователей: {metadata['statistics']['users']}")
            print(f"📚 Курсов: {metadata['statistics']['courses']}")
            
            # Проверка обязательных файлов
            required_files = [
                'database/database_dump_*.sql',
                'metadata.json'
            ]
            
            for file_pattern in required_files:
                if not any(f.startswith(file_pattern.split('*')[0]) for f in zip_file.namelist()):
                    print(f"❌ Отсутствует: {file_pattern}")
                    return False
            
            print("✅ Бэкап целостный")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

# Использование
check_backup_integrity('full_backup_20260512_135555.zip')
```

---

## 🚨 Предостережения

### ⚠️ Что нужно знать:
1. **Восстановление удаляет текущие данные**
2. **Проверяйте бэкапы перед восстановлением**
3. **Делайте тестовое восстановление**
4. **Храните бэкапы в разных местах**
5. **Используйте версионирование**

### 🔒 Безопасность:
- Храните бэкапы на отдельных носителях
- Шифруйте чувствительные данные
- Ограничьте доступ к бэкапам
- Регулярно тестируйте восстановление

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в админ-панели
2. Убедитесь в целостности ZIP-файла
3. Проверьте права доступа к файлам
4. Сделайте бэкап перед восстановлением

---

**🎯 Главное правило: Лучше иметь бэкап и не нуждаться, чем нуждаться и не иметь!**
