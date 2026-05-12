#!/usr/bin/env python
"""
Тестовый скрипт для отладки создания практического задания
"""
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, PracticeAssignment
from courses.forms import PracticeAssignmentForm
from courses.teacher_views import practice_assignment

User = get_user_model()

def test_assignment_creation():
    print("🔍 Начинаем тестирование создания практического задания...")
    
    # Создаем тестовые данные
    try:
        # Проверяем пользователя
        user = User.objects.first()
        if not user:
            print("❌ Нет пользователя в БД")
            return
        
        print(f"✅ Пользователь: {user.username}")
        
        # Проверяем курс
        course = Course.objects.first()
        if not course:
            print("❌ Нет курса в БД")
            return
        
        print(f"✅ Курс: {course.title}")
        
        # Проверяем урок
        lesson = course.lessons.filter(lesson_type='practice').first()
        if not lesson:
            print("❌ Нет урока типа practice")
            # Создаем тестовый урок
            lesson = Lesson.objects.create(
                course=course,
                title="Тестовый практический урок",
                lesson_type='practice',
                order=1
            )
            print(f"✅ Создан тестовый урок: {lesson.title}")
        else:
            print(f"✅ Урок: {lesson.title}")
        
        # Создаем RequestFactory
        factory = RequestFactory()
        
        # Тестовые данные формы
        form_data = {
            'title': 'Тестовое задание',
            'description': 'Тестовое описание',
            'requirements': 'Тестовые требования',
            'programming_language': 'python',
            'starter_code': 'print("Hello World")',
            'expected_output': 'Hello World',
            'time_limit': '5',
            'memory_limit': '256',
            'max_attempts': '10',
            'max_grade': '100',
            'require_manual_review': False,
            'is_published': True
        }
        
        # Тестовые данные для тестов
        test_data = {
            'test_input': ['input1', 'input2'],
            'test_output': ['output1', 'output2']
        }
        
        # Объединяем все данные
        post_data = {**form_data, **test_data}
        
        print(f"📝 POST данные: {post_data}")
        
        # Создаем запрос
        request = factory.post(f'/courses/teacher/lessons/{lesson.id}/practice/', post_data)
        request.user = user
        
        print(f"🌐 Создан запрос для урока {lesson.id}")
        
        # Пробуем создать форму
        try:
            form = PracticeAssignmentForm(post_data)
            print(f"📋 Форма создана")
            print(f"📋 Форма валидна: {form.is_valid()}")
            
            if not form.is_valid():
                print(f"❌ Ошибки формы: {form.errors}")
                for field, errors in form.errors.items():
                    print(f"   Поле {field}: {errors}")
                return
            
            print(f"✅ Форма валидна")
            
            # Пробуем сохранить
            try:
                assignment = form.save(commit=False)
                assignment.lesson = lesson
                assignment.save()
                print(f"✅ Assignment создан с ID: {assignment.id}")
                
                # Пробуем сохранить тесты
                try:
                    test_inputs = request.POST.getlist('test_input')
                    test_outputs = request.POST.getlist('test_output')
                    
                    print(f"🧪 test_inputs: {test_inputs}")
                    print(f"🧪 test_outputs: {test_outputs}")
                    
                    if test_outputs:
                        test_cases = []
                        for i, expected_output in enumerate(test_outputs):
                            if expected_output.strip():
                                input_data = test_inputs[i] if i < len(test_inputs) else ''
                                test_cases.append({
                                    'input': input_data.strip(),
                                    'expected_output': expected_output.strip()
                                })
                        
                        assignment.test_cases = test_cases
                        assignment.save()
                        
                        print(f"✅ Тесты сохранены: {len(test_cases)} шт.")
                        print(f"📊 assignment.test_cases: {assignment.test_cases}")
                    else:
                        print(f"⚠️ Нет test_outputs в запросе")
                    
                    print(f"🎉 Полное создание успешно!")
                    print(f"📊 Assignment ID: {assignment.id}")
                    print(f"📊 Title: {assignment.title}")
                    print(f"📊 Test cases: {assignment.test_cases}")
                    print(f"📊 Lesson: {assignment.lesson.title}")
                    
                    # Удаляем тестовые данные
                    assignment.delete()
                    print(f"🧹 Тестовый assignment удален")
                    
                except Exception as e:
                    print(f"❌ Ошибка при сохранении тестов: {e}")
                    import traceback
                    traceback.print_exc()
                
            except Exception as e:
                print(f"❌ Ошибка при сохранении assignment: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"❌ Ошибка при создании формы: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_assignment_creation()
