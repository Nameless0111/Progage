#!/usr/bin/env python
"""
Скрипт для полной очистки базы данных
Оставляет только пользователей с указанными email
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.db import connection
from accounts.models import User

def clean_database():
    """Полная очистка базы данных кроме указанных пользователей"""
    
    # Email пользователей которых нужно оставить
    allowed_emails = [
        'classnuychelovek@gmail.com',
        'lehaprorok228@gmail.com', 
        'pashokbilashenko@gmail.com'
    ]
    
    cursor = connection.cursor()
    
    try:
        print("🔍 Начинаем полную очистку базы данных...")
        
        # 1. Удаляем все таблицы в правильном порядке
        
        # Сначала удаляем все зависимости от курсов
        print("🗑️ Удаляем все записи на курсы...")
        cursor.execute("DELETE FROM courses_courseenrollment")
        cursor.execute("DELETE FROM courses_enrollment")
        
        print("🗑️ Удаляем все лайки...")
        cursor.execute("DELETE FROM courses_courselike")
        cursor.execute("DELETE FROM courses_like")
        
        print("🗑️ Удаляем все отзывы...")
        cursor.execute("DELETE FROM courses_coursereview")
        cursor.execute("DELETE FROM courses_review")
        
        print("🗑️ Удаляем все комментарии...")
        cursor.execute("DELETE FROM courses_lessoncomment")
        
        print("🗑️ Удаляем все результаты тестов...")
        cursor.execute("DELETE FROM courses_testanswersubmission")
        cursor.execute("DELETE FROM courses_testanswer")
        cursor.execute("DELETE FROM courses_testsubmission")
        cursor.execute("DELETE FROM courses_testquestion")
        
        print("🗑️ Удаляем все отправки кода...")
        cursor.execute("DELETE FROM courses_codesubmission")
        
        print("🗑️ Удаляем все практические задания...")
        cursor.execute("DELETE FROM courses_practiceassignment")
        
        print("🗑️ Удаляем все уроки...")
        cursor.execute("DELETE FROM courses_lesson")
        
        print("🗑️ Удаляем все курсы...")
        cursor.execute("DELETE FROM courses_course")
        
        print("🗑️ Удаляем все категории...")
        cursor.execute("DELETE FROM courses_category")
        
        # Удаляем все профили и настройки
        print("🗑️ Удаляем все профили...")
        cursor.execute("DELETE FROM accounts_profile")
        cursor.execute("DELETE FROM accounts_teacherrating")
        cursor.execute("DELETE FROM accounts_notification")
        cursor.execute("DELETE FROM accounts_password_reset")
        
        # Удаляем логи
        print("🗑️ Удаляем все логи...")
        cursor.execute("DELETE FROM adminpanel_errorlog")
        cursor.execute("DELETE FROM adminpanel_systemlog")
        cursor.execute("DELETE FROM adminpanel_backuplog")
        
        # Удаляем все чаты
        print("🗑️ Удаляем все чаты...")
        cursor.execute("DELETE FROM chat_message")
        cursor.execute("DELETE FROM chat_supportchat")
        
        # Удаляем всех пользователей кроме разрешенных
        print(f"🗑️ Удаляем всех пользователей кроме: {allowed_emails}")
        
        # Формируем условие для исключения разрешенных email
        placeholders = ','.join(['%s'] * len(allowed_emails))
        cursor.execute(f"""
            DELETE FROM accounts_user 
            WHERE email NOT IN ({placeholders})
        """, allowed_emails)
        
        # Проверяем сколько пользователей осталось
        cursor.execute("SELECT COUNT(*) FROM accounts_user")
        remaining_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT email FROM accounts_user")
        users = [row[0] for row in cursor.fetchall()]
        
        print(f"✅ Очистка завершена!")
        print(f"📊 Осталось пользователей: {remaining_users}")
        print(f"👤 Список оставшихся пользователей:")
        for user in users:
            print(f"   - {user}")
        
        connection.commit()
        print("✅ Все изменения сохранены")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        connection.rollback()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚨 ВНИМАНИЕ: ЭТО ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ!")
    print("📋 Будут удалены:")
    print("   • Все курсы")
    print("   • Все уроки")
    print("   • Все записи на курсы")
    print("   • Все отзывы и лайки")
    print("   • Все комментарии")
    print("   • Все результаты тестов")
    print("   • Все профили пользователей")
    print("   • Все логи")
    print("   • Все пользователи кроме:")
    print("     - classnuychelovek@gmail.com")
    print("     - lehaprorok228@gmail.com")
    print("     - pashokbilashenko@gmail.com")
    print()
    
    confirm = input("Вы уверены? (yes/no): ")
    if confirm.lower() == 'yes':
        clean_database()
    else:
        print("❌ Очистка отменена")
