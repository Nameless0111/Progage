#!/usr/bin/env python
"""
Тест для проверки API со статистикой
"""
import json
import os
import sys
import django

sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from django.test import Client

def test_api_stats():
    print("📊 Тест API со статистикой...")
    
    client = Client()
    
    # Тест 1: Простой код
    test_data = {
        'code': 'print("Hello, World!")',
        'language': 'python'
    }
    
    response = client.post(
        '/courses/api/test-code/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Успешно: {result['success']}")
        print(f"✅ Вывод: {result['output']}")
        print(f"✅ Время: {result['execution_time']} мс")
        print(f"✅ Память: {result['memory_usage']} МБ")
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(f"Content: {response.content.decode()}")
    
    # Тест 2: Код с ошибкой
    print("\n🧪 Тест с ошибкой...")
    test_data_error = {
        'code': 'print(undefined_variable)',
        'language': 'python'
    }
    
    response = client.post(
        '/courses/api/test-code/',
        data=json.dumps(test_data_error),
        content_type='application/json'
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Успешно: {result['success']}")
        print(f"✅ Ошибка: {result['error']}")
        print(f"✅ Время: {result['execution_time']} мс")
        print(f"✅ Память: {result['memory_usage']} МБ")

if __name__ == '__main__':
    test_api_stats()
