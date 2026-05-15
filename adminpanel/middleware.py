import logging
import json
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.http import JsonResponse
from .models import ActivityLog, UserSession, ErrorLog, SystemLog
import uuid

logger = logging.getLogger(__name__)

class LoggingMiddleware(MiddlewareMixin):
    SENSITIVE_HEADERS = {'authorization', 'cookie', 'x-csrftoken'}

    def process_request(self, request):
        request.request_id = str(uuid.uuid4())
        request.start_time = timezone.now()
        
        # Логирование всех запросов
        self._log_request(request)
        
        return None
    
    def process_response(self, request, response):
        # Логирование ответов
        self._log_response(request, response)
        
        # Логирование HTTP ошибок
        if hasattr(response, 'status_code') and response.status_code >= 400:
            self._log_http_error(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        # Логирование исключений
        self._log_exception(request, exception)
        return None
    
    def _log_request(self, request):
        """Логирование входящих запросов"""
        try:
            # Определение типа запроса
            request_type = 'HTTP'
            if request.path.startswith('/api/'):
                request_type = 'API'
            elif request.path.startswith('/admin/'):
                request_type = 'ADMIN'
            elif 'application/json' in request.content_type:
                request_type = 'JSON_API'
            
            # Логирование в SystemLog
            SystemLog.objects.create(
                level='INFO',
                message=f"[{request_type}] {request.method} {request.path}",
                module='middleware',
                function='process_request',
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request),
                extra_data={
                    'request_id': request.request_id,
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET),
                    'content_type': request.content_type,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'request_type': request_type,
                    'headers': self._safe_headers(request),
                }
            )
            
            # Дополнительное логирование для API запросов
            if request_type == 'API' or request_type == 'JSON_API':
                try:
                    body = request.body.decode('utf-8')
                    if body and len(body) < 10000:  # Ограничение размера
                        SystemLog.objects.create(
                            level='DEBUG',
                            message=f"[API_BODY] {request.method} {request.path}",
                            module='middleware',
                            function='log_api_body',
                            user=request.user if not isinstance(request.user, AnonymousUser) else None,
                            ip_address=self._get_client_ip(request),
                            extra_data={
                                'request_id': request.request_id,
                                'method': request.method,
                                'path': request.path,
                                'body': body,
                                'content_type': request.content_type,
                            }
                        )
                except Exception as e:
                    logger.error(f"Error logging API body: {e}")
            
        except Exception as e:
            logger.error(f"Error in _log_request: {e}")
    
    def _log_response(self, request, response):
        """Логирование ответов"""
        try:
            duration = (timezone.now() - request.start_time).total_seconds()
            
            # Определение типа ответа
            response_type = 'HTTP'
            if isinstance(response, JsonResponse):
                response_type = 'JSON'
            elif hasattr(response, 'Content-Type') and 'application/json' in response.get('Content-Type', ''):
                response_type = 'JSON'
            
            # Логирование медленных запросов
            if duration > 2.0:  # Запросы дольше 2 секунд
                SystemLog.objects.create(
                    level='WARNING',
                    message=f"[SLOW_REQUEST] {request.method} {request.path} - {duration:.2f}s",
                    module='middleware',
                    function='process_response',
                    user=request.user if not isinstance(request.user, AnonymousUser) else None,
                    ip_address=self._get_client_ip(request),
                    extra_data={
                        'request_id': request.request_id,
                        'method': request.method,
                        'path': request.path,
                        'duration': duration,
                        'status_code': getattr(response, 'status_code', 0),
                        'response_type': response_type,
                    }
                )
            
            # Логирование всех ответов
            SystemLog.objects.create(
                level='INFO',
                message=f"[{response_type}] {request.method} {request.path} -> {getattr(response, 'status_code', 0)}",
                module='middleware',
                function='process_response',
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request),
                extra_data={
                    'request_id': request.request_id,
                    'method': request.method,
                    'path': request.path,
                    'status_code': getattr(response, 'status_code', 0),
                    'duration': duration,
                    'response_type': response_type,
                    'content_length': len(getattr(response, 'content', b'')),
                }
            )
            
        except Exception as e:
            logger.error(f"Error in _log_response: {e}")
    
    def _log_http_error(self, request, response):
        """Логирование HTTP ошибок"""
        try:
            ErrorLog.objects.create(
                error_type=str(response.status_code),
                message=f"HTTP {response.status_code}: {request.method} {request.path}",
                url=request.get_full_path(),
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request)
            )
        except Exception as e:
            logger.error(f"Error in _log_http_error: {e}")
    
    def _log_exception(self, request, exception):
        """Логирование исключений"""
        try:
            ErrorLog.objects.create(
                error_type='EXCEPTION',
                message=str(exception),
                stack_trace=traceback.format_exc(),
                url=request.get_full_path(),
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request)
            )
        except Exception as e:
            logger.error(f"Error in _log_exception: {e}")
    
    def _get_client_ip(self, request):
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _safe_headers(self, request):
        """Возвращает заголовки без секретов сессии и авторизации."""
        headers = {}
        for name, value in request.headers.items():
            if name.lower() in self.SENSITIVE_HEADERS:
                headers[name] = '[redacted]'
            else:
                headers[name] = value
        return headers


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        """Логирование необработанных исключений"""
        try:
            ErrorLog.objects.create(
                error_type='UNHANDLED_EXCEPTION',
                message=str(exception),
                stack_trace=traceback.format_exc(),
                url=request.get_full_path(),
                user=request.user if not isinstance(request.user, AnonymousUser) else None,
                ip_address=self._get_client_ip(request)
            )
        except Exception as e:
            logger.error(f"Error in ExceptionLoggingMiddleware: {e}")
        
        return None
    
    def _get_client_ip(self, request):
        """Получение IP адреса клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ActivityLogger:
    """Класс для удобного логирования действий"""
    
    @staticmethod
    def log_action(user, action_type, object_type=None, object_id=None, object_repr=None, details=None, request=None):
        """Логирование действия пользователя"""
        try:
            ip_address = None
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
            
            ActivityLog.objects.create(
                user=user,
                action_type=action_type,
                object_type=object_type,
                object_id=object_id,
                object_repr=object_repr,
                details=details or {},
                ip_address=ip_address
            )
            
            # Дополнительное логирование в SystemLog
            SystemLog.objects.create(
                level='INFO',
                message=f"[ACTIVITY] {action_type}: {object_repr or 'N/A'}",
                module='activity_logger',
                function='log_action',
                user=user,
                ip_address=ip_address,
                extra_data={
                    'action_type': action_type,
                    'object_type': object_type,
                    'object_id': object_id,
                    'object_repr': object_repr,
                    'details': details or {},
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_action: {e}")
    
    @staticmethod
    def log_system_event(level, message, module='system', function='unknown', details=None, user=None):
        """Логирование системных событий"""
        try:
            SystemLog.objects.create(
                level=level,
                message=message,
                module=module,
                function=function,
                user=user,
                extra_data=details or {}
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_system_event: {e}")
    
    @staticmethod
    def log_api_call(user, method, endpoint, request_data=None, response_data=None, status_code=200, duration=0):
        """Логирование API вызовов"""
        try:
            ActivityLogger.log_system_event(
                level='INFO',
                message=f"[API_CALL] {method} {endpoint} -> {status_code} ({duration:.3f}s)",
                module='api_logger',
                function='log_api_call',
                user=user,
                extra_data={
                    'method': method,
                    'endpoint': endpoint,
                    'request_data': request_data,
                    'response_data': response_data,
                    'status_code': status_code,
                    'duration': duration,
                }
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_api_call: {e}")
    
    @staticmethod
    def log_terminal_command(user, command, working_directory=None, exit_code=None, output=None, error=None):
        """Логирование терминальных команд"""
        try:
            level = 'ERROR' if exit_code and exit_code != 0 else 'INFO'
            message = f"[TERMINAL] {command}"
            if exit_code is not None:
                message += f" -> {exit_code}"
            
            ActivityLogger.log_system_event(
                level=level,
                message=message,
                module='terminal_logger',
                function='log_terminal_command',
                user=user,
                extra_data={
                    'command': command,
                    'working_directory': working_directory,
                    'exit_code': exit_code,
                    'output': output,
                    'error': error,
                }
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_terminal_command: {e}")
    
    @staticmethod
    def log_database_query(user, query_type, table, query=None, duration=0, rows_affected=None):
        """Логирование запросов к базе данных"""
        try:
            level = 'WARNING' if duration > 1.0 else 'DEBUG'
            message = f"[DB_QUERY] {query_type} {table}"
            if duration > 0:
                message += f" ({duration:.3f}s)"
            if rows_affected is not None:
                message += f" - {rows_affected} rows"
            
            ActivityLogger.log_system_event(
                level=level,
                message=message,
                module='db_logger',
                function='log_database_query',
                user=user,
                extra_data={
                    'query_type': query_type,
                    'table': table,
                    'query': query,
                    'duration': duration,
                    'rows_affected': rows_affected,
                }
            )
        except Exception as e:
            logger.error(f"Error in ActivityLogger.log_database_query: {e}")
