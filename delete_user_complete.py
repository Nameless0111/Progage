#!/usr/bin/env python
"""
Полное удаление пользователя и всех связанных с ним данных
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.db import connection

def delete_user_complete(email):
    cursor = connection.cursor()
    
    try:
        # Находим пользователя
        cursor.execute('SELECT id FROM accounts_user WHERE email = %s', [email])
        user_result = cursor.fetchone()
        if user_result:
            user_id = user_result[0]
            print(f'✅ Найден пользователь ID: {user_id}')
            
            # Находим курсы пользователя
            cursor.execute('SELECT id FROM courses_course WHERE instructor_id = %s', [user_id])
            course_ids = [row[0] for row in cursor.fetchall()]
            print(f'✅ Найдено курсов: {course_ids}')
            
            if course_ids:
                # Удаляем все зависимости от курсов в правильном порядке
                
                # 1. Удаляем lessons
                cursor.execute('DELETE FROM courses_lesson WHERE course_id IN %s', [tuple(course_ids)])
                print('✅ Удалены уроки курсов')
                
                # 2. Удаляем courseenrollment_completed_lessons
                cursor.execute('DELETE FROM courses_courseenrollment_completed_lessons WHERE courseenrollment_id IN (SELECT id FROM courses_courseenrollment WHERE course_id IN %s)', [tuple(course_ids)])
                print('✅ Удалены completed lessons')
                
                # 3. Удаляем все enrollment таблицы
                cursor.execute('DELETE FROM courses_courseenrollment WHERE course_id IN %s', [tuple(course_ids)])
                print('✅ Удалены courseenrollment')
                
                cursor.execute('DELETE FROM courses_enrollment WHERE course_id IN %s', [tuple(course_ids)])
                print('✅ Удалены enrollment')
                
                # 4. Удаляем likes
                cursor.execute('DELETE FROM courses_courselike WHERE course_id IN %s', [tuple(course_ids)])
                print('✅ Удалены courselike')
                
                cursor.execute('DELETE FROM courses_like WHERE course_id IN %s', [tuple(course_ids)])
                print('✅ Удалены like')
                
                # 5. Удаляем reviews
                cursor.execute('DELETE FROM courses_coursereview WHERE course_id IN %s', [tuple(course_ids)])
                print('✅ Удалены coursereview')
                
                cursor.execute('DELETE FROM courses_review WHERE course_id IN %s', [tuple(course_ids)])
                print('✅ Удалены review')
                
                # 6. Удаляем practice assignments
                cursor.execute('DELETE FROM courses_practiceassignment WHERE lesson_id IN (SELECT id FROM courses_lesson WHERE course_id IN %s)', [tuple(course_ids)])
                print('✅ Удалены practice assignments')
                
                # 7. Удаляем test submissions
                cursor.execute('DELETE FROM courses_testsubmission WHERE lesson_id IN (SELECT id FROM courses_lesson WHERE course_id IN %s)', [tuple(course_ids)])
                print('✅ Удалены test submissions')
                
                # 8. Удаляем code submissions
                cursor.execute('DELETE FROM courses_codesubmission WHERE assignment_id IN (SELECT id FROM courses_practiceassignment WHERE lesson_id IN (SELECT id FROM courses_lesson WHERE course_id IN %s))', [tuple(course_ids)])
                print('✅ Удалены code submissions')
                
                # 9. Теперь удаляем сами курсы
                cursor.execute('DELETE FROM courses_course WHERE instructor_id = %s', [user_id])
                print(f'✅ Удалены курсы пользователя')
        
        # Удаляем error logs пользователя
        cursor.execute('DELETE FROM adminpanel_errorlog WHERE user_id = %s', [user_id])
        print('✅ Удалены error logs пользователя')
        
        # Удаляем system logs пользователя
        cursor.execute('DELETE FROM adminpanel_systemlog WHERE user_id = %s', [user_id])
        print('✅ Удалены system logs пользователя')
        
        # Удаляем самого пользователя
        cursor.execute('DELETE FROM accounts_user WHERE email = %s', [email])
        print(f'✅ Удален пользователь {email}')
        
        connection.commit()
        print('✅ Все изменения сохранены')
        
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        connection.rollback()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    email = "classnuychelovek@gmail.com"
    print(f"🔍 Начинаем полное удаление пользователя: {email}")
    delete_user_complete(email)
