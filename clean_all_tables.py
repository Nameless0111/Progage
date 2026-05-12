#!/usr/bin/env python
"""
Универсальный скрипт для очистки всех таблиц
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.db import connection

def clean_all_tables():
    """Очистка всех таблиц в правильном порядке"""
    
    # Email пользователей которых нужно оставить
    allowed_emails = [
        'classnuychelovek@gmail.com',
        'lehaprorok228@gmail.com', 
        'pashokbilashenko@gmail.com'
    ]
    
    cursor = connection.cursor()
    
    try:
        print("🔍 Начинаем полную очистку базы данных...")
        
        # Получаем все таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        all_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Найдено таблиц: {len(all_tables)}")
        
        # Исключаем таблицу migrations
        tables_to_clean = [t for t in all_tables if t != 'django_migrations']
        
        # Сначала удаляем все данные из таблиц кроме accounts_user
        for table in tables_to_clean:
            if table != 'accounts_user':
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    print(f"✅ Очищена таблица: {table}")
                except Exception as e:
                    print(f"⚠️ Пропущена таблица {table}: {e}")
        
        # Теперь удаляем всех пользователей кроме разрешенных
        print(f"🗑️ Удаляем всех пользователей кроме: {allowed_emails}")
        
        placeholders = ','.join(['%s'] * len(allowed_emails))
        cursor.execute(f"""
            DELETE FROM accounts_user 
            WHERE email NOT IN ({placeholders})
        """, allowed_emails)
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) FROM accounts_user")
        remaining_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT email, username FROM accounts_user")
        users = cursor.fetchall()
        
        print(f"✅ Очистка завершена!")
        print(f"📊 Осталось пользователей: {remaining_users}")
        print(f"👤 Список оставшихся пользователей:")
        for email, username in users:
            print(f"   - {username} ({email})")
        
        connection.commit()
        print("✅ Все изменения сохранены")
        
    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        connection.rollback()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚨 ВНИМАНИЕ: ЭТО ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ!")
    print("📋 Будут удалены ВСЕ данные из ВСЕХ таблиц!")
    print("👤 Останутся только пользователи:")
    print("   - classnuychelovek@gmail.com")
    print("   - lehaprorok228@gmail.com")
    print("   - pashokbilashenko@gmail.com")
    print()
    
    confirm = input("Вы уверены? (yes/no): ")
    if confirm.lower() == 'yes':
        clean_all_tables()
    else:
        print("❌ Очистка отменена")
