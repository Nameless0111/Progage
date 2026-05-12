#!/usr/bin/env python
"""
Тест простого вывода
"""
import os
import sys
import django

sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from courses.compiler_service import CodeCompiler

def test_simple_output():
    print("🔍 Тест простого вывода...")
    
    compiler = CodeCompiler()
    
    # Тест 1: Простой print
    print("\n🧪 Тест 1: Простой print('Hello')")
    result = compiler.compile_and_run('print("Hello")', 'python')
    print(f"success: {result.get('success')}")
    print(f"stdout: '{result.get('stdout')}'")
    print(f"stderr: '{result.get('stderr')}'")
    print(f"return_code: {result.get('return_code')}")
    print(f"status: {result.get('status')}")
    
    # Тест 2: Тестовый случай с пустым вводом
    print("\n🧪 Тест 2: Тестовый случай с пустым вводом")
    test_cases = [{'input': '', 'expected_output': 'Hello', 'timeout': 5}]
    result = compiler.run_test_cases('print("Hello")', 'python', test_cases)
    print(f"Всего тестов: {result.get('total_tests')}")
    print(f"Пройдено: {result.get('passed_tests')}")
    print(f"Провалено: {result.get('failed_tests')}")
    
    for test_result in result.get('test_results', []):
        print(f"  Тест {test_result['test_number']}: {'✅' if test_result['passed'] else '❌'}")
        print(f"    Вход: '{test_result['input']}'")
        print(f"    Ожидаемо: '{test_result['expected_output']}'")
        print(f"    Получено: '{test_result['actual_output']}'")
        print(f"    Статус: {test_result['status']}")
        print(f"    Ошибка: {test_result['error']}")
    
    # Тест 3: Тест с вводом
    print("\n🧪 Тест 3: Тест с вводом")
    code = '''
x = input()
print(x + " World")
'''
    test_cases = [{'input': 'Hello', 'expected_output': 'Hello World', 'timeout': 5}]
    result = compiler.run_test_cases(code, 'python', test_cases)
    print(f"Всего тестов: {result.get('total_tests')}")
    print(f"Пройдено: {result.get('passed_tests')}")
    print(f"Провалено: {result.get('failed_tests')}")
    
    for test_result in result.get('test_results', []):
        print(f"  Тест {test_result['test_number']}: {'✅' if test_result['passed'] else '❌'}")
        print(f"    Вход: '{test_result['input']}'")
        print(f"    Ожидаемо: '{test_result['expected_output']}'")
        print(f"    Получено: '{test_result['actual_output']}'")
        print(f"    Статус: {test_result['status']}")
        print(f"    Ошибка: {test_result['error']}")

if __name__ == '__main__':
    test_simple_output()
