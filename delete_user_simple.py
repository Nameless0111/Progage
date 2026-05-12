#!/usr/bin/env python
"""
Простой скрипт для удаления пользователя и всех связанных с ним данных
"""

import os
import django

# Устанавливаем переменные окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')

# Инициализируем Django
django.setup()

from accounts.models import User
from courses.models import Course, CourseEnrollment, CourseLike, CourseReview, LessonComment, TestSubmission, CodeSubmission

def delete_user_and_related_data(email):
    """Удаляет пользователя и все связанные с ним данные"""
    
    try:
        # Находим пользователя по email
        user = User.objects.get(email=email)
        username = user.username
        print(f"✅ Найден пользователь: {username} ({email})")
        
        # Сначала удаляем все CourseEnrollment из всей системы
        print("🗑️ Удаляем все записи на курсы...")
        CourseEnrollment.objects.all().delete()
        
        # Удаляем лайки на курсы
        likes = CourseLike.objects.filter(user=user)
        if likes.exists():
            print(f"🗑️ Найдено {likes.count()} лайков на курсы:")
            likes.delete()
        
        # Удаляем отзывы на курсы
        reviews = CourseReview.objects.filter(user=user)
        if reviews.exists():
            print(f"🗑️ Найдено {reviews.count()} отзывов на курсы:")
            reviews.delete()
        
        # Удаляем комментарии к урокам
        comments = LessonComment.objects.filter(user=user)
        if comments.exists():
            print(f"🗑️ Найдено {comments.count()} комментариев к урокам:")
            comments.delete()
        
        # Удаляем результаты тестов
        test_submissions = TestSubmission.objects.filter(user=user)
        if test_submissions.exists():
            print(f"🗑️ Найдено {test_submissions.count()} результатов тестов:")
            test_submissions.delete()
        
        # Удаляем отправки кода
        code_submissions = CodeSubmission.objects.filter(user=user)
        if code_submissions.exists():
            print(f"🗑️ Найдено {code_submissions.count()} отправок кода:")
            code_submissions.delete()
        
        # Теперь удаляем курсы преподавателя
        courses = Course.objects.filter(instructor=user)
        if courses.exists():
            print(f"🗑️ Найдено {courses.count()} курсов преподавателя:")
            for course in courses:
                print(f"   - {course.title}")
                course.delete()
        else:
            print("ℹ️ Курсы преподавателя не найдены")
        
        # Удаляем самого пользователя
        print(f"🗑️ Удаляем пользователя {username}...")
        user.delete()
        
        print(f"✅ Пользователь {email} и все связанные данные успешно удалены!")
        
    except User.DoesNotExist:
        print(f"❌ Пользователь с email {email} не найден")
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")

if __name__ == "__main__":
    email = "classnuychelovek@gmail.com"
    print(f"🔍 Начинаем удаление пользователя: {email}")
    delete_user_and_related_data(email)
