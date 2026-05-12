import os
import json
import zipfile
import shutil
from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.http import HttpResponse
from django.contrib.auth.models import User
from accounts.models import User as UserModel
from courses.models import Course, Lesson, CourseEnrollment, CourseLike, CourseReview
from chat.models import Message, SupportChat
from adminpanel.models import ActivityLog, SystemLog, ErrorLog, UserSession, BackupLog, PopularContent
from .models import BackupLog as AdminBackupLog


class SystemBackup:
    """Класс для создания полных бэкапов системы"""
    
    def __init__(self):
        # Создаем директорию для бэкапов в корне проекта
        self.backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Создание директории для бэкапов"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print(f"Создана директория для бэкапов: {self.backup_dir}")
    
    def get_backup_info(self):
        """Получить информацию о директории бэкапов"""
        return {
            'backup_dir': self.backup_dir,
            'exists': os.path.exists(self.backup_dir),
            'writable': os.access(self.backup_dir, os.W_OK) if os.path.exists(self.backup_dir) else False
        }
    
    def create_full_backup(self, user=None):
        """Создание полного бэкапа системы"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"full_backup_{timestamp}.zip"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        print(f"Начало создания бэкапа: {backup_filename}")
        print(f"Путь сохранения: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # 1. Бэкап базы данных
                print("Создание бэкапа базы данных...")
                self._backup_database(backup_zip)
                
                # 2. Бэкап медиафайлов
                print("Создание бэкапа медиафайлов...")
                self._backup_media_files(backup_zip)
                
                # 3. Бэкап конфигурационных файлов
                print("Создание бэкапа конфигурации...")
                self._backup_config_files(backup_zip)
                
                # 4. Бэкап логов
                print("Создание бэкапа логов...")
                self._backup_logs(backup_zip)
                
                # 5. Создание метаданных бэкапа
                print("Создание метаданных...")
                self._create_backup_metadata(backup_zip, timestamp)
            
            # Логирование создания бэкапа
            self._log_backup_creation(backup_filename, backup_path, user, True)
            
            file_size = os.path.getsize(backup_path)
            print(f"Бэкап успешно создан: {backup_filename} ({file_size} bytes)")
            
            return {
                'success': True,
                'filename': backup_filename,
                'path': backup_path,
                'size': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2),
                'timestamp': timestamp,
                'backup_dir': self.backup_dir
            }
            
        except Exception as e:
            print(f"Ошибка при создании бэкапа: {str(e)}")
            # Логирование ошибки
            self._log_backup_creation(backup_filename, backup_path, user, False, str(e))
            raise
    
    def _backup_database(self, backup_zip):
        """Бэкап базы данных"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Создание SQL дампа через Django management command
        sql_filename = f"database_dump_{timestamp}.sql"
        sql_path = os.path.join(self.backup_dir, sql_filename)
        
        try:
            # Используем команду Django для создания дампа
            with open(sql_path, 'w', encoding='utf-8') as f:
                call_command('dumpdata', '--natural-foreign', '--natural-primary', 
                           '--indent=2', stdout=f)
            
            backup_zip.write(sql_path, f"database/{sql_filename}")
            os.remove(sql_path)  # Удаляем временный файл
            print(f"База данных сохранена: {sql_filename}")
            
        except Exception as e:
            print(f"Ошибка при создании SQL дампа: {e}")
            # Альтернативный метод через прямой SQL
            self._backup_database_direct(backup_zip)
    
    def _backup_database_direct(self, backup_zip):
        """Прямой бэкап базы данных через SQL"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    print(f"Бэкап таблицы: {table_name}")
                    
                    cursor.execute(f"SELECT * FROM `{table_name}`")
                    rows = cursor.fetchall()
                    
                    # Получаем названия колонок
                    cursor.execute(f"DESCRIBE `{table_name}`")
                    columns = [col[0] for col in cursor.fetchall()]
                    
                    # Создаем JSON для таблицы
                    table_data = {
                        'table': table_name,
                        'columns': columns,
                        'rows': rows,
                        'row_count': len(rows)
                    }
                    
                    table_filename = f"database/table_{table_name}_{timestamp}.json"
                    backup_zip.writestr(table_filename, json.dumps(table_data, 
                                     ensure_ascii=False, indent=2, default=str))
        
        except Exception as e:
            print(f"Ошибка при прямом бэкапе БД: {e}")
            raise
    
    def _backup_media_files(self, backup_zip):
        """Бэкап медиафайлов"""
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        
        if media_root and os.path.exists(media_root):
            print(f"Бэкап медиафайлов из: {media_root}")
            
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, media_root)
                    backup_zip.write(file_path, f"media/{arcname}")
            
            print(f"Медиафайлы сохранены в архив")
        else:
            print("Директория медиафайлов не найдена")
    
    def _backup_config_files(self, backup_zip):
        """Бэкап конфигурационных файлов"""
        config_files = [
            'progage/settings.py',
            'progage/urls.py',
            'requirements.txt',
            'manage.py',
            '.env',
            'README.md'
        ]
        
        print("Бэкап конфигурационных файлов:")
        
        for config_file in config_files:
            if os.path.exists(config_file):
                backup_zip.write(config_file, f"config/{config_file}")
                print(f"  - {config_file}")
            else:
                print(f"  - {config_file} (не найден)")
    
    def _backup_logs(self, backup_zip):
        """Бэкап логов"""
        log_files = [
            'django.log',
            'debug.log', 
            'error.log',
            'access.log'
        ]
        
        print("Бэкап лог-файлов:")
        
        for log_file in log_files:
            if os.path.exists(log_file):
                backup_zip.write(log_file, f"logs/{log_file}")
                print(f"  - {log_file}")
            else:
                print(f"  - {log_file} (не найден)")
    
    def _create_backup_metadata(self, backup_zip, timestamp):
        """Создание метаданных бэкапа"""
        metadata = {
            'backup_type': 'full_system_backup',
            'timestamp': timestamp,
            'started_at': datetime.now().isoformat(),
            'django_version': getattr(settings, 'VERSION', 'unknown'),
            'python_version': os.sys.version,
            'backup_dir': self.backup_dir,
            'base_dir': settings.BASE_DIR,
            'database_settings': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
            },
            'media_root': getattr(settings, 'MEDIA_ROOT', None),
            'statistics': self._get_system_statistics()
        }
        
        backup_zip.writestr('metadata.json', json.dumps(metadata, 
                             ensure_ascii=False, indent=2, default=str))
        print("Метаданные бэкапа созданы")
    
    def _get_system_statistics(self):
        """Получение статистики системы"""
        try:
            stats = {
                'users': UserModel.objects.count(),
                'courses': Course.objects.count(),
                'lessons': Lesson.objects.count(),
                'enrollments': CourseEnrollment.objects.count(),
                'likes': CourseLike.objects.count(),
                'reviews': CourseReview.objects.count(),
                'messages': Message.objects.count(),
                'support_chats': SupportChat.objects.count(),
                'activity_logs': ActivityLog.objects.count(),
                'system_logs': SystemLog.objects.count(),
                'error_logs': ErrorLog.objects.count(),
                'user_sessions': UserSession.objects.count(),
                'backup_logs': AdminBackupLog.objects.count(),
            }
            print(f"Статистика системы собрана: {stats}")
            return stats
        except Exception as e:
            print(f"Ошибка при сборе статистики: {e}")
            return {'error': str(e)}
    
    def _log_backup_creation(self, filename, path, user, success, error=None):
        """Логирование создания бэкапа"""
        try:
            status = 'success' if success else 'failed'
            file_size = os.path.getsize(path) if success and os.path.exists(path) else 0
            
            from adminpanel.models import BackupLog
            
            BackupLog.objects.create(
                backup_type='full',
                status='completed' if success else 'failed',
                file_path=path,
                file_size=file_size,
                created_by=user,
                description=f"Полный бэкап системы: {filename}",
                error_message=error if not success else None
            )
            
            # Также логируем в системный лог
            from .middleware import ActivityLogger
            ActivityLogger.log_system_event(
                level='INFO' if success else 'ERROR',
                message=f"[BACKUP] {'Successfully created' if success else 'Failed to create'} backup: {filename}",
                module='backup_system',
                function='create_full_backup',
                user=user,
                details={
                    'filename': filename,
                    'path': path,
                    'status': status,
                    'file_size': file_size,
                    'backup_dir': self.backup_dir,
                    'error': error
                }
            )
            
        except Exception as e:
            print(f"Error logging backup creation: {e}")
    
    def list_backups(self):
        """Получение списка всех бэкапов"""
        backups = []
        
        if os.path.exists(self.backup_dir):
            print(f"Поиск бэкапов в директории: {self.backup_dir}")
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    
                    backup_info = {
                        'filename': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    }
                    backups.append(backup_info)
                    print(f"Найден бэкап: {filename} ({backup_info['size_mb']} MB)")
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def delete_backup(self, filename, user=None):
        """Удаление бэкапа"""
        try:
            file_path = os.path.join(self.backup_dir, filename)
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                
                print(f"Бэкап удален: {filename}")
                
                # Логирование удаления
                from adminpanel.models import BackupLog
                BackupLog.objects.create(
                    backup_type='delete',
                    file_path=file_path,
                    file_size=file_size,
                    status='completed',
                    created_by=user,
                    description=f"Удален бэкап: {filename}"
                )
                
                return True
            else:
                print(f"Файл бэкапа не найден: {file_path}")
                return False
                
        except Exception as e:
            print(f"Ошибка при удалении бэкапа: {e}")
            
            # Логирование ошибки
            from adminpanel.models import BackupLog
            BackupLog.objects.create(
                backup_type='delete',
                file_path=os.path.join(self.backup_dir, filename),
                status='failed',
                created_by=user,
                description=f"Ошибка при удалении бэкапа: {filename}",
                error_message=str(e)
            )
            return False
    
    def get_backup_path(self, filename):
        """Получить полный путь к файлу бэкапа"""
        return os.path.join(self.backup_dir, filename)
    
    def backup_exists(self, filename):
        """Проверить существование бэкапа"""
        file_path = self.get_backup_path(filename)
        return os.path.exists(file_path) and filename.endswith('.zip')
