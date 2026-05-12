import os
import sys
import json
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

class SystemBackup:
    """Класс для создания бэкапов системы"""
    
    def __init__(self):
        self.backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
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
                
                # 5. Создание метаданных
                print("Создание метаданных...")
                self._create_backup_metadata(backup_zip, timestamp)
            
            # Логирование успешного создания
            self._log_backup_creation(backup_filename, backup_path, user, True)
            
            file_size = os.path.getsize(backup_path)
            print(f"Бэкап успешно создан: {backup_filename} ({file_size} bytes)")
            
            return {
                'success': True,
                'filename': backup_filename,
                'path': backup_path,
                'size': file_size
            }
            
        except Exception as e:
            print(f"Error logging backup creation: {e}")
            self._log_backup_creation(backup_filename, backup_path, user, False, str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def _backup_database(self, backup_zip):
        """Бэкап базы данных"""
        from django.db import connection
        from django.core.management import execute_from_command_line
        import tempfile
        
        # Используем Django management команду для дампа
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.sql', delete=False) as temp_file:
            try:
                execute_from_command_line(['dumpdata', '--natural-foreign'], stdout=temp_file)
                temp_file.seek(0)
                sql_content = temp_file.read()
                backup_zip.writestr('database/database_dump_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.sql', sql_content)
            except Exception as e:
                print(f"Ошибка создания дампа БД: {e}")
                # Альтернативный метод
                pass
    
    def _backup_media_files(self, backup_zip):
        """Бэкап медиафайлов"""
        media_root = getattr(__import__('django.conf', 'settings', {}), 'MEDIA_ROOT', None)
        if media_root and os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        arcname = os.path.relpath(file_path, media_root)
                        backup_zip.write(file_path, arcname)
    
    def _backup_config_files(self, backup_zip):
        """Бэкап конфигурационных файлов"""
        config_files = [
            'progage/settings.py',
            'progage/urls.py',
            'requirements.txt',
            'manage.py',
            '.env'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                backup_zip.write(config_file, config_file)
    
    def _backup_logs(self, backup_zip):
        """Бэкап логов"""
        log_files = [
            'django.log',
            'debug.log',
            'error.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                backup_zip.write(log_file, log_file)
    
    def _create_backup_metadata(self, backup_zip, timestamp):
        """Создание метаданных бэкапа"""
        metadata = {
            'backup_type': 'full_system_backup',
            'timestamp': timestamp,
            'started_at': datetime.now().isoformat(),
            'django_version': getattr(__import__('django.conf', 'settings', {}), 'VERSION', 'unknown'),
            'python_version': sys.version,
            'platform': sys.platform,
            'statistics': self._get_statistics()
        }
        
        backup_zip.writestr('metadata.json', json.dumps(metadata, indent=2))
    
    def _get_statistics(self):
        """Сбор статистики системы"""
        try:
            from django.contrib.auth import get_user_model
            from courses.models import Course, CourseEnrollment, CourseLike, CourseReview
            from adminpanel.models import ActivityLog, SystemLog
            
            User = get_user_model()
            
            stats = {
                'users': User.objects.count(),
                'courses': Course.objects.count(),
                'enrollments': CourseEnrollment.objects.count(),
                'likes': CourseLike.objects.count(),
                'reviews': CourseReview.objects.count(),
                'activity_logs': ActivityLog.objects.count(),
                'system_logs': SystemLog.objects.count()
            }
            return stats
        except Exception as e:
            print(f"Ошибка при сборе статистики: {e}")
            return {'error': str(e)}
    
    def _log_backup_creation(self, filename, path, user, success, error=None):
        """Логирование создания бэкапа"""
        try:
            from adminpanel.models import BackupLog
            
            status = 'success' if success else 'failed'
            file_size = os.path.getsize(path) if success and os.path.exists(path) else 0
            
            BackupLog.objects.create(
                backup_type='full',
                status=status,
                file_path=path,
                file_size=file_size,
                created_by=user,
                description=f"Полный бэкап системы: {filename}",
                error_message=error if not success else None
            )
            
        except Exception as e:
            print(f"Error logging backup creation: {e}")
    
    def list_backups(self):
        """Получение списка всех бэкапов"""
        backups = []
        
        if os.path.exists(self.backup_dir):
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    backups.append({
                        'filename': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
