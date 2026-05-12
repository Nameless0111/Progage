#!/usr/bin/env python3
"""
Скрипт для очистки проекта от временных и тестовых файлов
Оставляет только основные файлы проекта
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Очистка проекта от временных файлов"""
    
    print("🧹 Очистка проекта от временных файлов...")
    
    # Файлы и папки для удаления
    files_to_remove = [
        # Временные папки
        "temp_restore",
        "temp_restore_*",
        
        # Тестовые скрипты
        "test_restore.py",
        "test_debug_cases.py",
        "test_test_cases.py",
        "test_browser_debug.py",
        "debug_sql.py",
        "restore_backup_fixed.py",
        "analyze_tables.py",
        "check_stats.py",
        "check_tables.py",
        "deactivate_user.py",
        
        # Временные файлы бэкапов
        "database_dump_*.sql",
        
        # Диагностические файлы
        "pages_to_check.md",
        
        # Дубликаты бэкапов (если есть)
        "backups/*_20260512_135555.zip",  # Старый бэкап
    ]
    
    # Файлы и папки для сохранения
    files_to_keep = [
        # Основные файлы проекта
        "manage.py",
        "requirements.txt",
        ".env",
        ".env.local",
        ".env.example",
        
        # Папки приложения
        "accounts",
        "adminpanel", 
        "courses",
        "progage",
        "chat",
        "templates",
        "static",
        "media",
        
        # Важные файлы конфигурации
        "progage/settings.py",
        "progage/urls.py",
        "progage/wsgi.py",
        
        # База данных
        "db.sqlite3",
        
        # Документация
        "README.md",
        "BACKUP_USAGE_GUIDE.md",
        
        # Папка бэкапов (но не файлы внутри)
        "backups/",
        
        # Виртуальное окружение
        "venv/",
        
        # Git файлы
        ".git/",
        ".gitignore",
        
        # Файлы для работы с бэкапами
        "restore_backup.py",
        "backup_utils.py",
    ]
    
    # Проверяем существование
    project_root = Path(".")
    removed_count = 0
    kept_count = 0
    
    print("\n📋 Проверка файлов...")
    
    # Сначала удаляем временные файлы
    for pattern in files_to_remove:
        if pattern.endswith("/") or pattern.endswith("\\"):
            # Это папка
            for item in project_root.glob(pattern):
                if item.is_dir():
                    try:
                        shutil.rmtree(item)
                        print(f"  🗑️ Удалена папка: {item}")
                        removed_count += 1
                    except Exception as e:
                        print(f"  ⚠️ Ошибка удаления папки {item}: {e}")
        else:
            # Это файл или маска
            for item in project_root.glob(pattern):
                if item.is_file():
                    try:
                        os.remove(item)
                        print(f"  🗑️ Удален файл: {item}")
                        removed_count += 1
                    except Exception as e:
                        print(f"  ⚠️ Ошибка удаления файла {item}: {e}")
    
    # Проверяем что основные файлы на месте
    print("\n✅ Проверка основных файлов...")
    for pattern in files_to_keep:
        if pattern.endswith("/") or pattern.endswith("\\"):
            # Это папка
            if not (project_root / pattern).exists():
                print(f"  ❌ Отсутствует папка: {pattern}")
        else:
            # Это файл или маска
            found = False
            for item in project_root.glob(pattern):
                if item.exists():
                    found = True
                    kept_count += 1
                    break
            if not found:
                print(f"  ❌ Отсутствует файл: {pattern}")
    
    # Очистка пустых папок в media
    media_dir = project_root / "media"
    if media_dir.exists():
        for item in media_dir.iterdir():
            item_path = media_dir / item
            if item_path.is_dir() and not any(item_path.glob("*")):
                try:
                    shutil.rmtree(item_path)
                    print(f"  🗑️ Удалена пустая папка: media/{item}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ⚠️ Ошибка удаления папки {item_path}: {e}")
    
    print(f"\n📊 Результат очистки:")
    print(f"  🗑️ Удалено файлов/папок: {removed_count}")
    print(f"  ✅ Сохранено файлов/папок: {kept_count}")
    
    # Показываем структуру проекта
    print(f"\n📁 Структура проекта после очистки:")
    show_project_structure()
    
    print(f"\n🎉 Очистка завершена!")
    print(f"\n💡 Основные файлы сохранены:")
    print(f"  - manage.py, requirements.txt, .env")
    print(f"  - Папки приложений (accounts, adminpanel, courses, progage, chat)")
    print(f"  - Шаблоны, статика, медиа")
    print(f"  - Файлы бэкапов и восстановления")
    print(f"  - Виртуальное окружение и Git")

def show_project_structure():
    """Показывает структуру проекта"""
    
    important_dirs = [
        "accounts/",
        "adminpanel/", 
        "courses/",
        "progage/",
        "chat/",
        "templates/",
        "static/",
        "media/",
        "backups/",
        "venv/"
    ]
    
    print("  📁 Основные папки:")
    for dir_name in important_dirs:
        if os.path.exists(dir_name):
            print(f"    ✅ {dir_name}")
        else:
            print(f"    ❌ {dir_name}")
    
    # Проверяем важные файлы
    important_files = [
        "manage.py",
        "requirements.txt", 
        ".env",
        "db.sqlite3",
        "restore_backup.py",
        "backup_utils.py"
    ]
    
    print("  📄 Важные файлы:")
    for file_name in important_files:
        if os.path.exists(file_name):
            size = os.path.getsize(file_name)
            print(f"    ✅ {file_name} ({size:,} bytes)")
        else:
            print(f"    ❌ {file_name}")

if __name__ == "__main__":
    print("🧹 Начинаю очистку проекта Progage...")
    print("⚠️  ВНИМАНИЕ! Будут удалены временные и тестовые файлы.")
    print("✅ Основные файлы проекта будут сохранены.")
    
    confirm = input("\nПродолжить очистку? (yes/no): ")
    if confirm.lower() == 'yes':
        cleanup_project()
    else:
        print("❌ Очистка отменена")
