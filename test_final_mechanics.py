#!/usr/bin/env python
"""
Финальный тест полной механики тестовых случаев
"""
import os
import sys
import django

sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, PracticeAssignment

User = get_user_model()

def test_final_mechanics():
    print("🎯 Финальный тест механики тестовых случаев...")
    
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
    
    # Назначаем инструктором
    if course.instructor != user:
        course.instructor = user
        course.save()
    
    # Создаем новый урок
    lesson = Lesson.objects.create(
        course=course,
        title="Финальный тестовый урок",
        lesson_type='practice',
        order=course.lessons.count() + 1
    )
    
    # Создаем клиент
    client = Client()
    client.force_login(user)
    
    print(f"📝 Урок: {lesson.title} (ID: {lesson.id})")
    
    # === ТЕСТ 1: Создание с одним тестом ===
    print("\n🧪 ТЕСТ 1: Создание с одним тестом")
    post_data = {
        'title': 'Задание с одним тестом',
        'description': 'Описание',
        'requirements': 'Требования',
        'programming_language': 'python',
        'starter_code': 'print("hello")',
        'expected_output': 'hello',
        'time_limit': '5',
        'memory_limit': '256',
        'max_attempts': '10',
        'max_grade': '100',
        'require_manual_review': 'False',
        'is_published': 'True',
        'test_input_0': '',
        'test_output_0': 'hello world',
    }
    
    response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=post_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 302:
        assignment = PracticeAssignment.objects.filter(lesson=lesson).first()
        if assignment:
            print(f"✅ Создано: {len(assignment.test_cases)} тестов")
            for i, test in enumerate(assignment.test_cases):
                print(f"  Тест {i+1}: {test}")
        else:
            print("❌ Assignment не создан")
    else:
        print(f"❌ Ошибка: {response.status_code}")
    
    # === ТЕСТ 2: Обновление с тремя тестами ===
    print("\n🧪 ТЕСТ 2: Обновление с тремя тестами")
    update_data = {
        'title': 'Задание с тремя тестами',
        'description': 'Описание',
        'requirements': 'Требования',
        'programming_language': 'python',
        'starter_code': 'print("hello")',
        'expected_output': 'hello',
        'time_limit': '5',
        'memory_limit': '256',
        'max_attempts': '10',
        'max_grade': '100',
        'require_manual_review': 'False',
        'is_published': 'True',
        'test_input_0': '',
        'test_output_0': 'hello world',
        'test_input_1': '5',
        'test_output_1': '10',
        'test_input_2': '10',
        'test_output_2': '20',
    }
    
    response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=update_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 302:
        assignment.refresh_from_db()
        print(f"✅ Обновлено: {len(assignment.test_cases)} тестов")
        for i, test in enumerate(assignment.test_cases):
            print(f"  Тест {i+1}: {test}")
    else:
        print(f"❌ Ошибка обновления: {response.status_code}")
    
    # === ТЕСТ 3: Удаление всех тестов ===
    print("\n🧪 ТЕСТ 3: Удаление всех тестов")
    empty_data = {
        'title': 'Задание без тестов',
        'description': 'Описание',
        'requirements': 'Требования',
        'programming_language': 'python',
        'starter_code': 'print("hello")',
        'expected_output': 'hello',
        'time_limit': '5',
        'memory_limit': '256',
        'max_attempts': '10',
        'max_grade': '100',
        'require_manual_review': 'False',
        'is_published': 'True',
        # НЕТ тестовых случаев!
    }
    
    response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=empty_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 302:
        assignment.refresh_from_db()
        print(f"✅ Пустые тесты: {len(assignment.test_cases)}")
        print(f"✅ test_cases: {assignment.test_cases}")
    else:
        print(f"❌ Ошибка очистки: {response.status_code}")
    
    # Удаляем тестовый урок
    lesson.delete()
    print("\n🧹 Тестовый урок удален")
    print("✅ Финальный тест завершен!")

if __name__ == '__main__':
    test_final_mechanics()
