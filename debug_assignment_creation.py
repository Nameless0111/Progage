#!/usr/bin/env python
"""
Детальное логирование создания практического задания
"""
import os
import sys
import django
import logging
from datetime import datetime

# Добавляем путь к проекту
sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assignment_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

from django.test import Client
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, PracticeAssignment
from courses.forms import PracticeAssignmentForm

User = get_user_model()

def log_request_details(request, title):
    """Логирование деталей запроса"""
    logger.info(f"\n{'='*50}")
    logger.info(f"{title}")
    logger.info(f"{'='*50}")
    logger.info(f"Метод: {request.method}")
    logger.info(f"URL: {request.get_full_path()}")
    logger.info(f"Пользователь: {request.user}")
    logger.info(f"Session: {dict(request.session)}")
    
    if request.method == 'POST':
        logger.info(f"POST данные:")
        for key, value in request.POST.items():
            if 'test' in key.lower():
                logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {key}: {value}")
        
        logger.info(f"FILES данные:")
        for key, value in request.FILES.items():
            logger.info(f"  {key}: {value}")

def test_with_logging():
    """Тест с подробным логированием"""
    logger.info("🔍 Начинаем детальное тестирование создания практического задания...")
    
    try:
        # Получаем пользователя
        user = User.objects.first()
        if not user:
            logger.error("❌ Нет пользователя в БД")
            return
        
        logger.info(f"✅ Пользователь найден: {user.username} (ID: {user.id})")
        
        # Получаем курс
        course = Course.objects.first()
        if not course:
            logger.error("❌ Нет курса в БД")
            return
        
        logger.info(f"✅ Курс найден: {course.title} (ID: {course.id})")
        logger.info(f"✅ Инструктор курса: {course.instructor}")
        
        # Назначаем пользователя инструктором если нужно
        if course.instructor != user:
            logger.warning("⚠️ Пользователь не инструктор, назначаем...")
            course.instructor = user
            course.save()
            logger.info(f"✅ Пользователь назначен инструктором")
        
        # Создаем новый урок типа practice для теста
        logger.info("🆕 Создаем новый урок типа practice для теста...")
        lesson = Lesson.objects.create(
            course=course,
            title=f"Тестовый практический урок {datetime.now().strftime('%H%M%S')}",
            lesson_type='practice',
            order=course.lessons.count() + 1
        )
        logger.info(f"✅ Создан новый урок: {lesson.title} (ID: {lesson.id})")
        
        # Создаем клиент
        client = Client()
        client.force_login(user)
        logger.info(f"✅ Клиент создан, пользователь залогинен")
        
        # Тест 1: GET запрос
        logger.info(f"\n📄 Тест 1: GET запрос страницы...")
        get_response = client.get(f'/courses/teacher/lessons/{lesson.id}/practice/')
        log_request_details(get_response.wsgi_request, "GET ЗАПРОС")
        logger.info(f"Статус GET: {get_response.status_code}")
        
        if get_response.status_code != 200:
            logger.error(f"❌ GET запрос failed: {get_response.status_code}")
            if get_response.status_code == 404:
                logger.error("URL не найден - проверьте URL patterns")
            return
        
        logger.info(f"✅ GET запрос успешен")
        
        # Тест 2: POST запрос с минимальными данными
        logger.info(f"\n📝 Тест 2: POST запрос с минимальными данными...")
        minimal_data = {
            'title': 'Минимальное задание',
            'description': 'Описание',
            'requirements': 'Требования',
            'programming_language': 'python',
            'starter_code': 'print("test")',
            'expected_output': 'test',
            'time_limit': '5',
            'memory_limit': '256',
            'max_attempts': '10',
            'max_grade': '100',
            'require_manual_review': 'False',
            'is_published': 'True'
        }
        
        post_response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=minimal_data)
        log_request_details(post_response.wsgi_request, "POST ЗАПРОС (минимальный)")
        logger.info(f"Статус POST: {post_response.status_code}")
        
        if post_response.status_code == 302:
            logger.info(f"✅ POST успешен, редирект на: {post_response.url}")
        else:
            logger.error(f"❌ POST failed: {post_response.status_code}")
            logger.error(f"Content: {post_response.content.decode()[:1000]}")
            
            # Проверяем ошибки формы
            if hasattr(post_response, 'context_data') and post_response.context_data:
                form = post_response.context_data.get('form')
                if form and hasattr(form, 'errors'):
                    logger.error(f"Ошибки формы: {form.errors}")
        
        # Проверяем результат
        assignment = PracticeAssignment.objects.filter(lesson=lesson).first()
        if assignment:
            logger.info(f"✅ Assignment создан: {assignment.title} (ID: {assignment.id})")
            logger.info(f"✅ Test cases: {assignment.test_cases}")
        else:
            logger.error(f"❌ Assignment не создан")
        
        # Тест 3: POST с тестами
        logger.info(f"\n📝 Тест 3: POST запрос с тестами...")
        
        # Удаляем предыдущий assignment
        if assignment:
            assignment.delete()
            logger.info(f"🧹 Предыдущий assignment удален")
        
        data_with_tests = {
            'title': 'Задание с тестами',
            'description': 'Описание',
            'requirements': 'Требования',
            'programming_language': 'python',
            'starter_code': 'print("test")',
            'expected_output': 'test',
            'time_limit': '5',
            'memory_limit': '256',
            'max_attempts': '10',
            'max_grade': '100',
            'require_manual_review': 'False',
            'is_published': 'True',
            'test_input': ['input1', 'input2', ''],
            'test_output': ['output1', 'output2', 'output3']
        }
        
        post_response_with_tests = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=data_with_tests)
        log_request_details(post_response_with_tests.wsgi_request, "POST ЗАПРОС (с тестами)")
        logger.info(f"Статус POST с тестами: {post_response_with_tests.status_code}")
        
        if post_response_with_tests.status_code == 302:
            logger.info(f"✅ POST с тестами успешен, редирект на: {post_response_with_tests.url}")
        else:
            logger.error(f"❌ POST с тестами failed: {post_response_with_tests.status_code}")
            logger.error(f"Content: {post_response_with_tests.content.decode()[:1000]}")
        
        # Проверяем результат с тестами
        assignment_with_tests = PracticeAssignment.objects.filter(lesson=lesson).first()
        if assignment_with_tests:
            logger.info(f"✅ Assignment с тестами создан: {assignment_with_tests.title}")
            logger.info(f"✅ Test cases: {assignment_with_tests.test_cases}")
            logger.info(f"✅ Test cases count: {len(assignment_with_tests.test_cases)}")
        else:
            logger.error(f"❌ Assignment с тестами не создан")
        
        # Тест 4: Проверка формы напрямую
        logger.info(f"\n📋 Тест 4: Проверка формы напрямую...")
        form = PracticeAssignmentForm(data=minimal_data)
        logger.info(f"Форма валидна: {form.is_valid()}")
        if not form.is_valid():
            logger.error(f"Ошибки формы: {form.errors}")
            for field, errors in form.errors.items():
                logger.error(f"  Поле {field}: {errors}")
        else:
            logger.info(f"✅ Форма валидна")
            
            # Пробуем сохранить
            try:
                test_assignment = form.save(commit=False)
                test_assignment.lesson = lesson
                test_assignment.save()
                logger.info(f"✅ Прямое сохранение успешно: ID {test_assignment.id}")
                test_assignment.delete()
            except Exception as e:
                logger.error(f"❌ Ошибка при сохранении: {e}")
                import traceback
                traceback.print_exc()
        
        # Удаляем тестовые данные
        if assignment_with_tests:
            assignment_with_tests.delete()
            logger.info(f"🧹 Тестовый assignment удален")
        
        logger.info(f"\n🎉 Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_with_logging()
