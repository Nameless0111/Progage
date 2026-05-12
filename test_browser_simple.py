#!/usr/bin/env python
"""
Простой тест через браузер с логированием
"""
import os
import sys
import django

sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson

User = get_user_model()

def test_browser_simple():
    print("🌐 Простой тест через браузер...")
    
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
        print("✅ Пользователь назначен инструктором")
    
    # Создаем новый урок
    lesson = Lesson.objects.create(
        course=course,
        title="Тестовый урок для проверки",
        lesson_type='practice',
        order=course.lessons.count() + 1
    )
    print(f"✅ Создан урок: {lesson.title} (ID: {lesson.id})")
    
    # Создаем клиент
    client = Client()
    client.force_login(user)
    
    # GET запрос
    print("\n📄 GET запрос...")
    response = client.get(f'/courses/teacher/lessons/{lesson.id}/practice/')
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ GET успешен")
        
        # POST запрос с минимальными данными
        print("\n📝 POST запрос...")
        post_data = {
            'title': 'Тестовое задание',
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
        
        response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=post_data)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ POST успешен, редирект")
            print(f"Redirect: {response.url}")
            
            # Проверяем assignment
            from courses.models import PracticeAssignment
            assignment = PracticeAssignment.objects.filter(lesson=lesson).first()
            if assignment:
                print(f"✅ Assignment создан: {assignment.title}")
            else:
                print("❌ Assignment не создан")
        else:
            print(f"❌ POST failed: {response.status_code}")
            print(f"Content: {response.content.decode()[:500]}")
    else:
        print(f"❌ GET failed: {response.status_code}")
    
    # Удаляем тестовый урок
    lesson.delete()
    print("🧹 Тестовый урок удален")

if __name__ == '__main__':
    test_browser_simple()
