"""
API views для курсов
"""
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


def api_test_page(request):
    """
    Debug-only page for taking a browser screenshot of the code test API.
    """
    host = request.get_host().split(':', 1)[0].lower()
    is_localhost = host in {'localhost', '127.0.0.1', '::1'}

    if not settings.DEBUG and not is_localhost:
        raise Http404

    return render(request, 'courses/api_test_page.html')


@csrf_exempt
@require_http_methods(["POST"])
def test_code(request):
    """
    API endpoint для проверки кода с использованием улучшенного компилятора
    """
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        if not code.strip():
            return JsonResponse({
                'success': False,
                'error': 'Код не может быть пустым'
            })
        
        # Используем улучшенный компилятор
        from .compiler_service import compiler
        
        result = compiler.compile_and_run(code, language)
        
        # Форматируем ответ для совместимости с frontend
        return JsonResponse({
            'success': result['success'],
            'output': result['stdout'] if result['stdout'] else None,
            'error': result['stderr'] if result['stderr'] else None,
            'execution_time': round(result['execution_time'] * 1000) if result['execution_time'] else 0,  # в миллисекундах
            'memory_usage': result.get('memory_used', 0),  # в МБ
            'status': result['status'],
            'error_details': result.get('error_details')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Внутренняя ошибка: {str(e)}',
            'execution_time': None,
            'memory_usage': None
        })
