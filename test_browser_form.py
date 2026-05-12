#!/usr/bin/env python
"""
Тест для проверки формы через браузер
"""
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson

User = get_user_model()

def test_browser_form():
    print("🌐 Тестирование формы через браузер...")
    
    try:
        # Получаем пользователя
        user = User.objects.first()
        if not user:
            print("❌ Нет пользователя")
            return
        
        # Получаем курс
        course = Course.objects.first()
        if not course:
            print("❌ Нет курса")
            return
        
        # Получаем урок типа practice
        lesson = course.lessons.filter(lesson_type='practice').first()
        if not lesson:
            print("⚠️ Нет урока типа practice, создаем тестовый...")
            # Создаем тестовый урок типа practice
            lesson = Lesson.objects.create(
                course=course,
                title="Тестовый практический урок",
                lesson_type='practice',
                order=course.lessons.count() + 1
            )
            print(f"✅ Создан тестовый урок: {lesson.title} (ID: {lesson.id})")
        
        print(f"✅ Пользователь: {user.username}")
        print(f"✅ Курс: {course.title}")
        print(f"✅ Инструктор курса: {course.instructor}")
        print(f"✅ Пользователь инструктор: {course.instructor == user}")
        print(f"✅ Урок: {lesson.title} (ID: {lesson.id})")
        print(f"✅ Тип урока: {lesson.lesson_type}")
        
        # Проверяем, является ли пользователь инструктором
        if course.instructor != user:
            print("❌ Пользователь не является инструктором курса!")
            # Делаем пользователя инструктором для теста
            course.instructor = user
            course.save()
            print("✅ Пользователь назначен инструктором курса")
        
        # Если урок не practice, создаем новый
        if lesson.lesson_type != 'practice':
            print("⚠️ Урок не типа practice, создаем новый...")
            lesson = Lesson.objects.create(
                course=course,
                title="Тестовый практический урок",
                lesson_type='practice',
                order=course.lessons.count() + 1
            )
            print(f"✅ Создан практический урок: {lesson.title} (ID: {lesson.id})")
        
        # Создаем клиент
        client = Client()
        client.force_login(user)
        
        # Тест 1: GET запрос страницы
        print(f"\n📄 Тест 1: GET запрос страницы...")
        response = client.get(f'/courses/teacher/lessons/{lesson.id}/practice/')
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            print("✅ GET запрос успешен")
        else:
            print(f"❌ GET запрос failed: {response.status_code}")
            return
        
        # Тест 2: POST запрос без тестов
        print(f"\n📝 Тест 2: POST запрос без тестов...")
        form_data = {
            'title': 'Тестовое задание без тестов',
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
        
        response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=form_data)
        print(f"Статус: {response.status_code}")
        if response.status_code == 302:
            print("✅ POST запрос успешен (редирект)")
            print(f"Redirect to: {response.url}")
        else:
            print(f"❌ POST запрос failed: {response.status_code}")
            print(f"Content: {response.content.decode()[:500]}")
            return
        
        # Проверяем, создался ли assignment
        from courses.models import PracticeAssignment
        assignment = PracticeAssignment.objects.filter(lesson=lesson).first()
        if assignment:
            print(f"✅ Assignment создан: {assignment.title}")
            print(f"✅ Test cases: {assignment.test_cases}")
        else:
            print("❌ Assignment не создан")
        
        # Тест 3: POST запрос с тестами
        print(f"\n📝 Тест 3: POST запрос с тестами...")
        
        # Удаляем предыдущий assignment
        if assignment:
            assignment.delete()
            print("🧹 Предыдущий assignment удален")
        
        form_data_with_tests = {
            'title': 'Тестовое задание с тестами',
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
            'test_input': ['input1', 'input2'],
            'test_output': ['output1', 'output2']
        }
        
        response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=form_data_with_tests)
        print(f"Статус: {response.status_code}")
        if response.status_code == 302:
            print("✅ POST запрос с тестами успешен (редирект)")
            print(f"Redirect to: {response.url}")
        else:
            print(f"❌ POST запрос с тестами failed: {response.status_code}")
            print(f"Content: {response.content.decode()[:500]}")
            return
        
        # Проверяем assignment с тестами
        assignment = PracticeAssignment.objects.filter(lesson=lesson).first()
        if assignment:
            print(f"✅ Assignment создан: {assignment.title}")
            print(f"✅ Test cases: {assignment.test_cases}")
            print(f"✅ Test cases count: {len(assignment.test_cases)}")
        else:
            print("❌ Assignment не создан")
        
        # Удаляем тестовый assignment
        if assignment:
            assignment.delete()
            print("🧹 Тестовый assignment удален")
        
        print(f"\n🎉 Все тесты пройдены!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_browser_form()
