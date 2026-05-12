#!/usr/bin/env python
"""
Финальный тест исправлений
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

def test_final_fix():
    print("🎯 Финальный тест исправлений...")
    
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
    
    # === ТЕСТ 1: Создание с тестовыми случаями ===
    print("\n🧪 ТЕСТ 1: Создание с тестовыми случаями")
    post_data = {
        'title': 'Задание с тестами',
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
        
        # Тестовые случаи
        'test_input_0': '',
        'test_output_0': 'Hello World',
        'test_input_1': '5',
        'test_output_1': '10',
        'test_input_2': '10',
        'test_output_2': '15',
    }
    
    response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=post_data)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 302:
        assignment = PracticeAssignment.objects.filter(lesson=lesson).first()
        if assignment:
            print(f"✅ Создано: {len(assignment.test_cases)} тестов")
            for i, test in enumerate(assignment.test_cases):
                print(f"  Тест {i+1}: input='{test['input']}', output='{test['expected_output']}'")
            
            # Проверяем что содержимое сохранено правильно
            if assignment.test_cases[0]['expected_output'] == 'Hello World':
                print("✅ Содержимое тестов сохранено правильно!")
            else:
                print("❌ Содержимое тестов не сохранено!")
        else:
            print("❌ Assignment не создан")
    else:
        print(f"❌ Ошибка: {response.status_code}")
    
    # Удаляем тестовый урок
    lesson.delete()
    print("\n🧹 Тестовый урок удален")
    print("✅ Финальный тест завершен!")

if __name__ == '__main__':
    test_final_fix()
