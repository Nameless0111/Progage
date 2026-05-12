#!/usr/bin/env python
"""
Исправление роли админа
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from accounts.models import User

def fix_admin_role():
    """Исправление роли админа"""
    
    try:
        # Находим админа
        admin = User.objects.get(email='pashokbilashenko335@gmail.com')
        
        # Исправляем роль
        admin.role = 'admin'
        admin.save()
        
        print("✅ Роль админа исправлена!")
        print(f"👤 Имя пользователя: {admin.username}")
        print(f"📧 Email: {admin.email}")
        print(f"🎓 Роль: {admin.role}")
        print(f"👑 Статус: Суперадмин")
        
    except User.DoesNotExist:
        print("❌ Админ не найден")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    fix_admin_role()
