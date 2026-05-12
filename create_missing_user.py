#!/usr/bin/env python
"""
Создание недостающего пользователя
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from accounts.models import User

def create_missing_user():
    """Создание пользователя pashokbilashenko@gmail.com"""
    
    try:
        # Проверяем существует ли пользователь
        if User.objects.filter(email='pashokbilashenko@gmail.com').exists():
            print("ℹ️ Пользователь pashokbilashenko@gmail.com уже существует")
            user = User.objects.get(email='pashokbilashenko@gmail.com')
            print(f"👤 Имя пользователя: {user.username}")
            return
        
        # Создаем пользователя
        user = User.objects.create_user(
            username='pashokbilashenko',
            email='pashokbilashenko@gmail.com',
            password='password123',  # Временный пароль
            first_name='Павел',
            last_name='Билашенко',
            role='teacher'
        )
        
        print("✅ Пользователь pashokbilashenko@gmail.com создан успешно!")
        print(f"👤 Имя пользователя: {user.username}")
        print(f"📧 Email: {user.email}")
        print(f"🎓 Роль: {user.role}")
        print(f"🔑 Пароль: password123 (временный)")
        
    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {e}")

if __name__ == "__main__":
    create_missing_user()
