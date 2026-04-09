#!/usr/bin/env python
"""
Простой запуск сервера Progage с проверкой настроек
"""
import os
import sys
import subprocess
import webbrowser
import socket

def check_settings():
    """Проверка настроек"""
    print("🔍 Проверка настроек...")
    
    try:
        from progage.settings import ALLOWED_HOSTS, RECAPTCHA_PUBLIC_KEY
        print(f"✅ ALLOWED_HOSTS: {ALLOWED_HOSTS}")
        
        if RECAPTCHA_PUBLIC_KEY and '6LfsPK4sAAAAAMixYec' in RECAPTCHA_PUBLIC_KEY:
            print("✅ reCAPTCHA: настроен с твоими ключами")
        else:
            print("⚠️ reCAPTCHA: проверь ключи")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка настроек: {e}")
        return False

def start_server():
    """Запуск сервера"""
    print("🚀 Запуск Django сервера...")
    
    # Собираем статику
    try:
        result = subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'], 
                          capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Статика собрана")
        else:
            print("⚠️ Ошибка сборки статики")
    except:
        print("⚠️ Не удалось собрать статику")
    
    # Запускаем сервер
    try:
        subprocess.Popen(['python', 'manage.py', 'runserver', '0.0.0.0:8000'])
        print("✅ Сервер запущен!")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False

def get_local_ip():
    """Получение локального IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    """Основная функция"""
    print("🌐 Запуск Progage сервера")
    
    # Проверяем настройки
    if not check_settings():
        input("\nНажми Enter для выхода...")
        return
    
    # Запускаем сервер
    if not start_server():
        input("\nНажми Enter для выхода...")
        return
    
    local_ip = get_local_ip()
    
    # Открываем браузер
    try:
        webbrowser.open(f'http://{local_ip}:8000')
        print(f"🌐 Браузер открыт: http://{local_ip}:8000")
    except:
        pass
    
    print(f"\n🎉 Готово!")
    print(f"📍 Сервер работает на: http://{local_ip}:8000")
    print(f"🤖 reCAPTCHA настроена")
    print(f"📱 Доступ с телефона по тому же адресу")
    print(f"\n💡 Для доступа из интернета:")
    print(f"   ngrok http 8000")
    print(f"\n🛑 Остановка: Ctrl+C")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
