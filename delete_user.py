#!/usr/bin/env python
"""
Скрипт для удаления пользователя и всех связанных с ним данных
"""

import os
import django

# Устанавливаем переменные окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')

# Инициализируем Django
django.setup()

from accounts.models import User, Profile, TeacherRating
from courses.models import Course, CourseEnrollment, CourseLike, CourseReview, LessonComment, TestSubmission, CodeSubmission

def delete_user_and_related_data(email):
    """Удаляет пользователя и все связанные с ним данные"""
    
    try:
        # Находим пользователя по email
        user = User.objects.get(email=email)
        username = user.username
        print(f"✅ Найден пользователь: {username} ({email})")
        
        # Удаляем связанные профили
        try:
            profile = user.profile
            print(f"🗑️ Удаляем Profile...")
            profile.delete()
        except Profile.DoesNotExist:
            print("ℹ️ Profile не найден")
        
        try:
            teacher_rating = TeacherRating.objects.filter(user=user).first()
            if teacher_rating:
                print(f"🗑️ Удаляем TeacherRating...")
                teacher_rating.delete()
            else:
                print("ℹ️ TeacherRating не найден")
        except Exception as e:
            print(f"ℹ️ Ошибка при удалении TeacherRating: {e}")
        
        # Сначала удаляем все записи на курсы пользователя
        enrollments = CourseEnrollment.objects.filter(user=user)
        if enrollments.exists():
            print(f"🗑️ Найдено {enrollments.count()} записей на курсы:")
            for enrollment in enrollments:
                print(f"   - {enrollment.course.title}")
            enrollments.delete()
        else:
            print("ℹ️ Записи на курсы не найдены")
        
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
                
                # Удаляем оставшиеся зависимости от курса
                CourseEnrollment.objects.filter(course=course).delete()
                CourseLike.objects.filter(course=course).delete()
                CourseReview.objects.filter(course=course).delete()
                LessonComment.objects.filter(lesson__course=course).delete()
                TestSubmission.objects.filter(lesson__course=course).delete()
                CodeSubmission.objects.filter(assignment__lesson__course=course).delete()
                
                # Теперь удаляем сам курс
                course.delete()
        else:
            print("ℹ️ Курсы преподавателя не найдены")
        
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
