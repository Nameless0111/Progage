#!/usr/bin/env python
"""
Тест новой механики тестовых случаев
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

def test_new_test_cases():
    print("🧪 Тест новой механики тестовых случаев...")
    
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
        title="Тестовый урок для новой механики",
        lesson_type='practice',
        order=course.lessons.count() + 1
    )
    
    # Создаем клиент
    client = Client()
    client.force_login(user)
    
    # GET запрос
    response = client.get(f'/courses/teacher/lessons/{lesson.id}/practice/')
    print(f"GET статус: {response.status_code}")
    
    if response.status_code == 200:
        # POST запрос с тестовыми случаями
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
            'is_published': 'True',
            # Тестовые случаи
            'test_input_0': '',
            'test_output_0': 'Hello World',
            'test_input_1': '5',
            'test_output_1': '8',
            'test_input_2': '10',
            'test_output_2': '15',
            'test_input_3': '20',
            'test_output_3': '25',
        }
        
        response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=post_data)
        print(f"POST статус: {response.status_code}")
        
        if response.status_code == 302:
            # Проверяем assignment
            assignment = PracticeAssignment.objects.filter(lesson=lesson).first()
            if assignment:
                print(f"✅ Assignment создан: {assignment.title}")
                print(f"✅ Тип test_cases: {type(assignment.test_cases)}")
                print(f"✅ Количество тестов: {len(assignment.test_cases)}")
                print(f"✅ Тестовые случаи: {assignment.test_cases}")
                
                # Проверяем каждый тест
                for i, test_case in enumerate(assignment.test_cases):
                    print(f"  Тест {i+1}: input='{test_case['input']}', output='{test_case['expected_output']}'")
                
                # Тест обновления
                print("\n🔄 Тест обновления...")
                update_data = post_data.copy()
                update_data['test_input_4'] = '30'
                update_data['test_output_4'] = '35'
                
                response = client.post(f'/courses/teacher/lessons/{lesson.id}/practice/', data=update_data)
                if response.status_code == 302:
                    assignment.refresh_from_db()
                    print(f"✅ Обновлено! Количество тестов: {len(assignment.test_cases)}")
                    for i, test_case in enumerate(assignment.test_cases):
                        print(f"  Тест {i+1}: input='{test_case['input']}', output='{test_case['expected_output']}'")
                else:
                    print(f"❌ Ошибка обновления: {response.status_code}")
            else:
                print("❌ Assignment не создан")
        else:
            print(f"❌ POST failed: {response.status_code}")
            if response.status_code == 200:
                # Показываем ошибки формы
                print("Ошибки формы:")
                print(response.content.decode())
    else:
        print(f"❌ GET failed: {response.status_code}")
    
    # Удаляем тестовый урок
    lesson.delete()
    print("🧹 Тестовый урок удален")

if __name__ == '__main__':
    test_new_test_cases()
