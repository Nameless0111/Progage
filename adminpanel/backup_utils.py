import json
import logging
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management import call_command

from accounts.models import User as UserModel
from adminpanel.models import ActivityLog, BackupLog as AdminBackupLog, ErrorLog, SystemLog, UserSession
from chat.models import Message, SupportChat
from courses.models import Course, CourseEnrollment, CourseLike, CourseReview, Lesson

logger = logging.getLogger(__name__)


class SystemBackup:
    """Создание и управление архивами бэкапов."""

    def __init__(self):
        self.backup_dir = Path(getattr(settings, 'BACKUP_ROOT', settings.BASE_DIR / 'backups')).resolve()
        self.ensure_backup_directory()

    def ensure_backup_directory(self):
        """Создает директорию для бэкапов с правами, подходящими для Linux."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.backup_dir.chmod(0o750)
        except OSError:
            logger.debug("Could not chmod backup directory %s", self.backup_dir, exc_info=True)

    def get_backup_info(self):
        """Возвращает информацию о директории бэкапов."""
        return {
            'backup_dir': str(self.backup_dir),
            'exists': self.backup_dir.exists(),
            'writable': os.access(self.backup_dir, os.W_OK),
        }

    def create_full_backup(self, user=None):
        """Создает полный архив: база, media, конфигурация, логи и metadata."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'full_backup_{timestamp}.zip'
        backup_path = self.backup_dir / backup_filename

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                self._backup_database(backup_zip, timestamp)
                self._backup_media_files(backup_zip)
                self._backup_config_files(backup_zip)
                self._backup_logs(backup_zip)
                self._create_backup_metadata(backup_zip, timestamp)

            file_size = backup_path.stat().st_size
            self._log_backup_creation(backup_filename, backup_path, user, True)
            logger.info("Backup created: %s (%s bytes)", backup_filename, file_size)

            return {
                'success': True,
                'filename': backup_filename,
                'path': str(backup_path),
                'size': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2),
                'timestamp': timestamp,
                'backup_dir': str(self.backup_dir),
            }

        except Exception as error:
            logger.exception("Backup creation failed: %s", backup_filename)
            self._log_backup_creation(backup_filename, backup_path, user, False, str(error))
            return {
                'success': False,
                'error': str(error),
                'filename': backup_filename,
            }

    def _backup_database(self, backup_zip, timestamp):
        """Сохраняет переносимый JSON-дамп Django ORM."""
        dump_name = f'database_dump_{timestamp}.json'

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.json', delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            with temp_path.open('w', encoding='utf-8') as output:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--indent=2',
                    stdout=output,
                )
            backup_zip.write(temp_path, f'database/{dump_name}')
        finally:
            temp_path.unlink(missing_ok=True)

    def _backup_media_files(self, backup_zip):
        """Добавляет пользовательские файлы из MEDIA_ROOT."""
        media_root = Path(getattr(settings, 'MEDIA_ROOT', '')).resolve()
        if not media_root.exists():
            return

        for file_path in media_root.rglob('*'):
            if file_path.is_file():
                arcname = Path('media') / file_path.relative_to(media_root)
                backup_zip.write(file_path, arcname.as_posix())

    def _backup_config_files(self, backup_zip):
        """Добавляет публичные конфиги без секретов окружения."""
        config_files = [
            'progage/settings.py',
            'progage/urls.py',
            'progage/asgi.py',
            'progage/wsgi.py',
            'requirements.txt',
            'manage.py',
            '.env.example',
            'README.md',
        ]

        for config_file in config_files:
            file_path = Path(settings.BASE_DIR) / config_file
            if file_path.exists() and file_path.is_file():
                backup_zip.write(file_path, f'config/{Path(config_file).as_posix()}')

    def _backup_logs(self, backup_zip):
        """Добавляет логи приложения из LOG_DIR и корневые *.log файлы."""
        log_roots = [
            Path(getattr(settings, 'LOG_DIR', settings.BASE_DIR / 'logs')).resolve(),
            Path(settings.BASE_DIR).resolve(),
        ]

        seen = set()
        for log_root in log_roots:
            if not log_root.exists():
                continue

            log_files = log_root.rglob('*.log') if log_root.is_dir() else []
            for file_path in log_files:
                resolved = file_path.resolve()
                if resolved in seen or not resolved.is_file():
                    continue
                seen.add(resolved)
                arcname = Path('logs') / resolved.name
                backup_zip.write(resolved, arcname.as_posix())

    def _create_backup_metadata(self, backup_zip, timestamp):
        """Добавляет metadata.json с техническими сведениями без секретов."""
        metadata = {
            'backup_type': 'full_system_backup',
            'timestamp': timestamp,
            'started_at': datetime.now().isoformat(),
            'platform': os.name,
            'backup_dir': str(self.backup_dir),
            'base_dir': str(settings.BASE_DIR),
            'database_engine': settings.DATABASES['default']['ENGINE'],
            'media_root': str(getattr(settings, 'MEDIA_ROOT', '')),
            'statistics': self._get_system_statistics(),
        }

        backup_zip.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2, default=str))

    def _get_system_statistics(self):
        """Собирает краткую статистику системы."""
        try:
            return {
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
        except Exception as error:
            logger.exception("Could not collect backup statistics")
            return {'error': str(error)}

    def _log_backup_creation(self, filename, path, user, success, error=None):
        """Пишет событие создания бэкапа в БД."""
        try:
            file_size = path.stat().st_size if success and path.exists() else 0
            AdminBackupLog.objects.create(
                backup_type='full',
                status='completed' if success else 'failed',
                file_path=str(path),
                file_size=file_size,
                created_by=user,
                description=f'Полный бэкап системы: {filename}',
                error_message=error if not success else None,
            )

            from .middleware import ActivityLogger

            ActivityLogger.log_system_event(
                level='INFO' if success else 'ERROR',
                message=f"[BACKUP] {'Created' if success else 'Failed'} backup: {filename}",
                module='backup_system',
                function='create_full_backup',
                user=user,
                details={
                    'filename': filename,
                    'path': str(path),
                    'status': 'completed' if success else 'failed',
                    'file_size': file_size,
                    'backup_dir': str(self.backup_dir),
                    'error': error,
                },
            )
        except Exception:
            logger.exception("Could not log backup creation")

    def list_backups(self):
        """Возвращает список zip-бэкапов."""
        backups = []
        if not self.backup_dir.exists():
            return backups

        for file_path in self.backup_dir.glob('*.zip'):
            if not file_path.is_file():
                continue

            stat = file_path.stat()
            backups.append({
                'filename': file_path.name,
                'path': str(file_path),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / 1024 / 1024, 2),
                'created': datetime.fromtimestamp(stat.st_mtime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
            })

        return sorted(backups, key=lambda item: item['modified'], reverse=True)

    def delete_backup(self, filename, user=None):
        """Удаляет zip-бэкап, не позволяя выйти за BACKUP_ROOT."""
        try:
            file_path = self._resolve_backup_path(filename)
            file_size = file_path.stat().st_size
            file_path.unlink()

            AdminBackupLog.objects.create(
                backup_type='delete',
                file_path=str(file_path),
                file_size=file_size,
                status='completed',
                created_by=user,
                description=f'Удален бэкап: {filename}',
            )
            return True

        except Exception as error:
            logger.exception("Could not delete backup: %s", filename)
            AdminBackupLog.objects.create(
                backup_type='delete',
                file_path=str(self.backup_dir / filename),
                status='failed',
                created_by=user,
                description=f'Ошибка при удалении бэкапа: {filename}',
                error_message=str(error),
            )
            return False

    def get_backup_path(self, filename):
        """Возвращает абсолютный путь к zip-бэкапу."""
        return str(self._resolve_backup_path(filename))

    def backup_exists(self, filename):
        """Проверяет существование zip-бэкапа."""
        try:
            return self._resolve_backup_path(filename).is_file()
        except ValueError:
            return False

    def _resolve_backup_path(self, filename):
        """Проверяет имя файла и не допускает path traversal."""
        if Path(filename).name != filename or not filename.endswith('.zip'):
            raise ValueError('Некорректное имя файла бэкапа')

        file_path = (self.backup_dir / filename).resolve()
        if self.backup_dir not in file_path.parents:
            raise ValueError('Путь бэкапа выходит за разрешенную директорию')
        if not file_path.exists():
            raise FileNotFoundError(filename)
        return file_path
