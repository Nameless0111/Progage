#!/usr/bin/env python
"""
Простой скрипт для бэкапа локальной PostgreSQL
"""
import os
import subprocess
import datetime
import gzip

def backup_database():
    """Создание бэкапа базы данных"""
    
    # Параметры подключения
    db_config = {
        'user': 'progage_user',
        'password': '1111',
        'host': 'localhost',
        'port': '5432',
        'database': 'progage_db'
    }
    
    # Имя файла с датой
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'progage_backup_{timestamp}.sql'
    compressed_filename = f'{filename}.gz'
    
    print(f"📦 Создание бэкапа: {filename}")
    
    # Команда для создания дампа
    cmd = [
        'pg_dump',
        f'--host={db_config["host"]}',
        f'--port={db_config["port"]}',
        f'--username={db_config["user"]}',
        f'--dbname={db_config["database"]}',
        '--no-owner',
        '--no-privileges',
        '--verbose',
        '--format=custom',
        f'--file={filename}'
    ]
    
    # Устанавливаем переменную окружения для пароля
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    try:
        # Выполняем команду
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Бэкап создан: {filename}")
            
            # Сжимаем файл
            with open(filename, 'rb') as f_in:
                with gzip.open(compressed_filename, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Удаляем несжатый файл
            os.remove(filename)
            
            print(f"📦 Бэкап сжат: {compressed_filename}")
            print(f"📊 Размер: {os.path.getsize(compressed_filename)} байт")
            
            return compressed_filename
        else:
            print(f"❌ Ошибка создания бэкапа: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print("❌ pg_dump не найден. Установите PostgreSQL или добавьте pg_dump в PATH.")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def restore_database(backup_file):
    """Восстановление базы данных из бэкапа"""
    
    db_config = {
        'user': 'progage_user',
        'password': '1111',
        'host': 'localhost',
        'port': '5432',
        'database': 'progage_db'
    }
    
    print(f"🔄 Восстановление из: {backup_file}")
    
    # Распаковываем если нужно
    if backup_file.endswith('.gz'):
        import gzip
        uncompressed_file = backup_file[:-3]
        with gzip.open(backup_file, 'rb') as f_in:
            with open(uncompressed_file, 'wb') as f_out:
                f_out.write(f_in.read())
        backup_file = uncompressed_file
    
    # Команда для восстановления
    cmd = [
        'pg_restore',
        f'--host={db_config["host"]}',
        f'--port={db_config["port"]}',
        f'--username={db_config["user"]}',
        f'--dbname={db_config["database"]}',
        '--clean',
        '--if-exists',
        '--verbose',
        backup_file
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ База данных восстановлена")
        else:
            print(f"❌ Ошибка восстановления: {result.stderr}")
            
    except FileNotFoundError:
        print("❌ pg_restore не найден. Установите PostgreSQL.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) > 2:
            restore_database(sys.argv[2])
        else:
            print("Использование: python backup_local_db.py restore <backup_file>")
    else:
        backup_database()
