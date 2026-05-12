#!/usr/bin/env python
"""
Скрипт для удаления пользователя и всех связанных с ним данных
Сначала удаляет все CourseEnrollment, потом курсы
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
        
        # СНАЧАЛА УДАЛЯЕМ ВСЕ CourseEnrollment из всей системы
        print("🗑️ Удаляем ВСЕ записи на курсы из системы...")
        all_enrollments = CourseEnrollment.objects.all()
        if all_enrollments.exists():
            enrollments_deleted = all_enrollments.delete()
            print(f"✅ Удалено {enrollments_deleted[0]} записей на курсы из всей системы")
        else:
            print("ℹ️ Записей на курсы не найдено")
        
        # Удаляем лайки на курсы
        likes = CourseLike.objects.filter(user=user)
        if likes.exists():
            likes_deleted = likes.delete()
            print(f"🗑️ Удалено {likes_deleted[0]} лайков на курсы")
        
        # Удаляем отзывы на курсы
        reviews = CourseReview.objects.filter(user=user)
        if reviews.exists():
            reviews_deleted = reviews.delete()
            print(f"🗑️ Удалено {reviews_deleted[0]} отзывов на курсы")
        
        # Удаляем комментарии к урокам
        comments = LessonComment.objects.filter(user=user)
        if comments.exists():
            comments_deleted = comments.delete()
            print(f"🗑️ Удалено {comments_deleted[0]} комментариев к урокам")
        
        # Удаляем результаты тестов
        test_submissions = TestSubmission.objects.filter(user=user)
        if test_submissions.exists():
            test_deleted = test_submissions.delete()
            print(f"🗑️ Удалено {test_deleted[0]} результатов тестов")
        
        # Удаляем отправки кода
        code_submissions = CodeSubmission.objects.filter(user=user)
        if code_submissions.exists():
            code_deleted = code_submissions.delete()
            print(f"🗑️ Удалено {code_deleted[0]} отправок кода")
        
        # Теперь удаляем курсы преподавателя
        courses = Course.objects.filter(instructor=user)
        if courses.exists():
            print(f"🗑️ Удаляем {courses.count()} курсов преподавателя:")
            for course in courses:
                print(f"   - {course.title}")
            courses_deleted = courses.delete()
            print(f"✅ Удалено {courses_deleted[0]} курсов")
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    email = "classnuychelovek@gmail.com"
    print(f"🔍 Начинаем удаление пользователя: {email}")
    delete_user_and_related_data(email)
