#!/usr/bin/env python
"""
Проверка таблиц чата
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.db import connection

def check_chat_tables():
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'chat_%'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print('Таблицы чата:')
        for table in tables:
            print(f'  {table}')
            
    except Exception as e:
        print(f'Ошибка: {e}')

if __name__ == "__main__":
    check_chat_tables()
