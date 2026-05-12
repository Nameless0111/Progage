#!/usr/bin/env python
"""
Тест исправления KeyError в compiler_service
"""
import os
import sys
import django

sys.path.append('c:/Progage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'progage.settings')
django.setup()

from courses.compiler_service import CodeCompiler

def test_compiler_fix():
    print("🔧 Тест исправления KeyError в compiler_service...")
    
    compiler = CodeCompiler()
    
    # Тест 1: Проверка безопасности - должна вернуть stdout
    print("\n🧪 Тест 1: Проверка безопасности")
    result = compiler.compile_and_run("import os; os.system('ls')", "python")
    print(f"Ключи в результате: {list(result.keys())}")
    print(f"stdout в результате: {'stdout' in result}")
    print(f"success: {result.get('success')}")
    print(f"error: {result.get('error')}")
    
    # Тест 2: Неподдерживаемый язык - должна вернуть stdout
    print("\n🧪 Тест 2: Неподдерживаемый язык")
    result = compiler.compile_and_run("print('hello')", "unsupported_lang")
    print(f"Ключи в результате: {list(result.keys())}")
    print(f"stdout в результате: {'stdout' in result}")
    print(f"success: {result.get('success')}")
    print(f"error: {result.get('error')}")
    
    # Тест 3: Нормальный код - должна вернуть stdout
    print("\n🧪 Тест 3: Нормальный код")
    result = compiler.compile_and_run("print('Hello, World!')", "python")
    print(f"Ключи в результате: {list(result.keys())}")
    print(f"stdout в результате: {'stdout' in result}")
    print(f"success: {result.get('success')}")
    print(f"stdout: {result.get('stdout')}")
    
    # Тест 4: Запуск тестовых случаев
    print("\n🧪 Тест 4: Запуск тестовых случаев")
    test_cases = [
        {'input': '5', 'expected_output': '10', 'timeout': 5},
        {'input': '10', 'expected_output': '15', 'timeout': 5}
    ]
    
    code = """
def add(a, b):
    return a + b

x = int(input())
print(x + 5)
"""
    
    result = compiler.run_test_cases(code, "python", test_cases)
    print(f"Ключи в результате: {list(result.keys())}")
    print(f"Всего тестов: {result.get('total_tests')}")
    print(f"Пройдено: {result.get('passed_tests')}")
    print(f"Провалено: {result.get('failed_tests')}")
    
    for test_result in result.get('test_results', []):
        print(f"  Тест {test_result['test_number']}: {'✅' if test_result['passed'] else '❌'}")
        print(f"    Вход: '{test_result['input']}'")
        print(f"    Ожидаемо: '{test_result['expected_output']}'")
        print(f"    Получено: '{test_result['actual_output']}'")
    
    print("\n✅ Тест завершен!")

if __name__ == '__main__':
    test_compiler_fix()
