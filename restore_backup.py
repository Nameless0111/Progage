#!/usr/bin/env python3
"""
Скрипт для восстановления системы из бэкапа Progage
Использование: python restore_backup.py <backup_file.zip>
"""

import os
import sys
import shutil
import sqlite3
import json
import zipfile
import subprocess
import re
from pathlib import Path
from datetime import datetime

def restore_backup(backup_path):
    """Полное восстановление из бэкапа"""
    
    print(f"🔄 Восстановление из: {backup_path}")
    
    # Проверка файла
    if not os.path.exists(backup_path):
        print(f"❌ Файл не найден: {backup_path}")
        print(f"💡 Убедитесь что файл существует или укажите полный путь:")
        print(f"   python restore_backup.py backups/{os.path.basename(backup_path)}")
        return False
    
    # Создаем временную директорию
    extract_dir = Path("temp_restore")
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir()
    
    try:
        # 1. Распаковка архива
        print("📦 Распаковка архива...")
        with zipfile.ZipFile(backup_path, 'r') as zip_file:
            zip_file.extractall(extract_dir)
            
        # 2. Проверка метаданных
        metadata_file = extract_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print(f"📅 Дата создания бэкапа: {metadata.get('created_at', 'Unknown')}")
            print(f"👥 Пользователей: {metadata.get('statistics', {}).get('users', 0)}")
            print(f"📚 Курсов: {metadata.get('statistics', {}).get('courses', 0)}")
            print(f"📝 Уроков: {metadata.get('statistics', {}).get('lessons', 0)}")
        else:
            print("⚠️ Метаданные не найдены")
        
        # Подтверждение восстановления
        confirm = input("\n⚠️  ВНИМАНИЕ! Это удалит все текущие данные. Продолжить? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Восстановление отменено")
            return False
        
        # 3. Резервная копия текущих данных
        print("💾 Создание резервной копии текущих данных...")
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Резервная копия базы данных
        if os.path.exists("db.sqlite3"):
            shutil.copy2("db.sqlite3", f"db.sqlite3.backup_{backup_timestamp}")
        
        # Резервная копия медиафайлов
        if os.path.exists("media"):
            shutil.move("media", f"media_backup_{backup_timestamp}")
        
        # Резервная копия конфигурации
        config_files = [
            ("progage/settings.py", f"progage/settings.py.backup_{backup_timestamp}"),
            (".env", f".env.backup_{backup_timestamp}"),
            ("requirements.txt", f"requirements.txt.backup_{backup_timestamp}")
        ]
        
        for src, dst in config_files:
            if os.path.exists(src):
                shutil.copy2(src, dst)
        
        # 4. Восстановление базы данных
        print("🗄️ Восстановление базы данных...")
        db_dir = extract_dir / "database"
        if db_dir.exists():
            sql_files = list(db_dir.glob("*.sql"))
            if sql_files:
                sql_file = sql_files[0]  # Берем первый SQL файл
                
                # Удаляем текущую базу
                if os.path.exists("db.sqlite3"):
                    os.remove("db.sqlite3")
                
                # Восстанавливаем из дампа с улучшенной обработкой JSON
                conn = sqlite3.connect("db.sqlite3")
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                        
                    print("🔧 Обработка SQL дампа...")
                    
                    # Разделяем SQL на отдельные INSERT statements
                    sql_statements = []
                    current_statement = ""
                    
                    for line in sql_content.split('\n'):
                        line = line.strip()
                        if not line or line.startswith('--'):
                            continue
                        
                        # Если строка начинается с INSERT, начинаем новый statement
                        if line.upper().startswith('INSERT'):
                            if current_statement.strip():
                                sql_statements.append(current_statement.strip())
                            current_statement = line
                        else:
                            current_statement += " " + line
                    
                    # Добавляем последний statement
                    if current_statement.strip():
                        sql_statements.append(current_statement.strip())
                    
                    print(f"📝 Найдено SQL statements: {len(sql_statements)}")
                    
                    # Выполняем каждый statement отдельно
                    success_count = 0
                    for i, statement in enumerate(sql_statements):
                        try:
                            # Дополнительная очистка JSON данных и исправление синтаксиса
                            statement = re.sub(r'"session_data":\s*\'([^\']*)\'', 
                                            lambda m: '"session_data": \'' + m.group(1).replace("'", "''") + '\'', 
                                            statement)
                            
                            conn.execute(statement)
                            success_count += 1
                            
                            if success_count % 100 == 0:
                                print(f"🔄 Обработано {success_count}/{len(sql_statements)} statements...")
                                
                        except Exception as e:
                            # Пропускаем проблемные statement, но продолжаем
                            print(f"⚠️ Пропущен statement {i+1}: {str(e)[:100]}...")
                            continue
                    
                    conn.commit()
                    print(f"✅ База данных восстановлена: {success_count}/{len(sql_statements)} statements выполнены")
                    
                except Exception as e:
                    print(f"⚠️ Ошибка при восстановлении SQL: {e}")
                    print("🔄 Попытка простого восстановления...")
                    try:
                        # Пробуем выполнить SQL как есть (без обработки JSON)
                        conn.executescript(sql_content)
                        conn.commit()
                        print("✅ База данных восстановлена (базовый метод)")
                    except Exception as e2:
                        print(f"❌ Ошибка при базовом восстановлении: {e2}")
                finally:
                    conn.close()
            else:
                print("⚠️ SQL дамп не найден в бэкапе")
        else:
            print("⚠️ Директория database не найдена в бэкапе")
        
        # 5. Восстановление медиафайлов
        print("📁 Восстановление медиафайлов...")
        media_backup_dir = extract_dir / "media"
        if media_backup_dir.exists():
            # Для Windows используем robocopy или xcopy
            if os.name == 'nt':
                try:
                    subprocess.run(['robocopy', str(media_backup_dir), 'media', '/E'], check=True)
                    print("✅ Медиафайлы восстановлены (robocopy)")
                except:
                    # Fallback to xcopy
                    subprocess.run(['xcopy', str(media_backup_dir), 'media', '/E', '/I', '/Y'], check=False)
                    print("✅ Медиафайлы восстановлены (xcopy)")
            else:
                # Для Unix систем
                shutil.copytree(media_backup_dir, "media")
                print("✅ Медиафайлы восстановлены")
        else:
            print("⚠️ Медиафайлы не найдены в бэкапе")
        
        # 6. Восстановление конфигурации
        print("⚙️ Восстановление конфигурации...")
        config_backup_dir = extract_dir / "config"
        if config_backup_dir.exists():
            config_files_restore = [
                ("progage/settings.py", "progage/settings.py"),
                (".env", ".env"),
                ("requirements.txt", "requirements.txt"),
                ("manage.py", "manage.py"),
                ("README.md", "README.md")
            ]
            
            for src, dst in config_files_restore:
                src_path = config_backup_dir / src
                if src_path.exists():
                    shutil.copy2(src_path, dst)
                    print(f"✅ {src} восстановлен")
        else:
            print("⚠️ Конфигурационные файлы не найдены в бэкапе")
        
        # 7. Установка зависимостей
        print("📦 Установка зависимостей...")
        requirements_file = extract_dir / "config" / "requirements.txt"
        if requirements_file.exists():
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print("✅ Зависимости установлены")
                else:
                    print(f"⚠️ Некоторые зависимости не установлены:")
                    # Показываем только важные ошибки, не весь вывод
                    error_lines = result.stderr.split('\n')
                    for line in error_lines[-10:]:  # Последние 10 строк ошибок
                        if 'error' in line.lower() or 'failed' in line.lower():
                            print(f"   {line.strip()}")
                    
                    # Проверяем критические зависимости
                    critical_deps = ['django', 'pillow', 'python-decouple']
                    missing_critical = []
                    
                    try:
                        import django
                    except ImportError:
                        missing_critical.append('django')
                    
                    try:
                        import pillow
                    except ImportError:
                        missing_critical.append('pillow')
                    
                    try:
                        import decouple
                    except ImportError:
                        missing_critical.append('python-decouple')
                    
                    if missing_critical:
                        print(f"❌ Критические зависимости отсутствуют: {', '.join(missing_critical)}")
                        print("🔧 Установите их вручную: pip install django pillow python-decouple")
                        return False
                    else:
                        print("✅ Критические зависимости в порядке (mysqlclient опционален)")
                        
            except subprocess.TimeoutExpired:
                print("⚠️ Установка зависимостей превысила время (5 минут)")
            except Exception as e:
                print(f"⚠️ Ошибка установки зависимостей: {e}")
                print("💡 Попробуйте установить вручную: pip install -r requirements.txt")
        else:
            print("⚠️ Файл requirements.txt не найден")
        
        # 8. Очистка
        print("🧹 Очистка временных файлов...")
        shutil.rmtree(extract_dir)
        
        print("\n✅ Восстановление завершено успешно!")
        print("\n🚀 Дальнейшие шаги:")
        print("1. Запустите миграции: python manage.py migrate")
        print("2. Создайте суперпользователя: python manage.py createsuperuser")

def check_backup_integrity(backup_path):
    """Проверка целостности бэкапа"""
    try:
        with zipfile.ZipFile(backup_path, 'r') as zip_file:
            files = zip_file.namelist()
            
            # Проверка обязательных файлов
            required_patterns = [
                'database/',
                'metadata.json'
            ]
            
            missing_files = []
            for pattern in required_patterns:
                if not any(f.startswith(pattern.rstrip('/')) for f in files):
                    missing_files.append(pattern)
            
            if missing_files:
                print(f"❌ Отсутствуют обязательные файлы: {missing_files}")
                return False
            
            # Проверка метаданных
            if 'metadata.json' in files:
                try:
                    metadata = json.loads(zip_file.read('metadata.json'))
                    print(f"📊 Бэкап от: {metadata.get('created_at', 'Unknown')}")
                    print(f"👥 Пользователей: {metadata.get('statistics', {}).get('users', 'Unknown')}")
                    print(f"📚 Курсов: {metadata.get('statistics', {}).get('courses', 'Unknown')}")
                except json.JSONDecodeError:
                    print("⚠️ Метаданные повреждены")
            
            print("✅ Цостостность бэкапа проверена")
            return True
            
    except zipfile.BadZipFile:
        print("❌ Поврежденный ZIP-архив")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

def main():
    if len(sys.argv) != 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print("Использование: python restore_backup.py <backup_file.zip>")
        print("Пример: python restore_backup.py full_backup_20260512_135555.zip")
        print("Или: python restore_backup.py backups/full_backup_20260512_135555.zip")
        print("")
        print("Скрипт автоматически ищет файлы в папке backups/")
        print("Если файл находится в другой папке, укажите полный путь")
        sys.exit(0 if sys.argv[1] in ['-h', '--help', 'help'] else 1)
    
    backup_filename = sys.argv[1]
    
    # Если указано только имя файла, ищем в папке backups/
    if not os.path.sep in backup_filename and not backup_filename.startswith('backups/') and not backup_filename.startswith('backups\\'):
        backup_path = os.path.join('backups', backup_filename)
    else:
        backup_path = backup_filename
    
    # Проверка целостности
    print("🔍 Проверка целостности бэкапа...")
    if not check_backup_integrity(backup_path):
        print("❌ Бэкап поврежден или неполный")
        sys.exit(1)
    
    # Восстановление
    if restore_backup(backup_path):
        print("\n🎉 Система успешно восстановлена!")
    else:
        print("\n❌ Восстановление не удалось")
        sys.exit(1)

if __name__ == "__main__":
    main()
