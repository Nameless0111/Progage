#!/usr/bin/env python
"""
Восстановление админа pashokbilashenko335@gmail.com
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from accounts.models import User

def restore_admin():
    """Восстановление админа"""
    
    try:
        # Проверяем существует ли пользователь
        if User.objects.filter(email='pashokbilashenko335@gmail.com').exists():
            print("ℹ️ Админ pashokbilashenko335@gmail.com уже существует")
            user = User.objects.get(email='pashokbilashenko335@gmail.com')
            print(f"👤 Имя пользователя: {user.username}")
            return
        
        # Создаем админа
        user = User.objects.create_superuser(
            username='admin',
            email='pashokbilashenko335@gmail.com',
            password='admin123',  # Временный пароль
            first_name='Админ',
            last_name='Системы'
        )
        
        print("✅ Админ pashokbilashenko335@gmail.com восстановлен!")
        print(f"👤 Имя пользователя: {user.username}")
        print(f"📧 Email: {user.email}")
        print(f"🎓 Роль: {user.role}")
        print(f"🔑 Пароль: admin123 (временный)")
        print(f"👑 Статус: Суперадмин")
        
    except Exception as e:
        print(f"❌ Ошибка при восстановлении админа: {e}")

if __name__ == "__main__":
    restore_admin()
