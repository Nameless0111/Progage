
"""
Безопасный сервис компиляции кода с изолированной средой
"""

import os
import subprocess
import tempfile
import shutil
import time
import re
import shlex
import sys

from typing import Dict, List, Tuple
from .models import SecurityConfig


class CodeCompiler:
    """Безопасный компилятор кода с песочницей"""

    NOFILE_LIMIT = 256

    MIN_RUNTIME_MEMORY_MB = {
        'python': 128,
        'javascript': 4096,
        'java': 4096,
        'cpp': 256,
        'c': 256,
    }

    MIN_COMPILE_MEMORY_MB = {
        'java': 4096,
        'cpp': 512,
        'c': 512,
    }

    DEFAULT_CONFIGS = {
        'python': {
            'compile_command': '',
            'run_command': 'python3 {file}',
            'file_extension': 'py',
            'max_execution_time': 5,
            'max_memory': 256,
            'allowed_libraries': [
                'math',
                'random',
                'string',
                'datetime',
                'collections'
            ],
            'forbidden_patterns': [
                r'import\s+os',
                r'import\s+sys',
                r'import\s+subprocess',
                r'import\s+socket',
                r'import\s+urllib',
                r'import\s+requests',
                r'import\s+shutil',
                r'import\s+tempfile',
                r'import\s+pathlib',
                r'__import__',
                r'eval\s*\(',
                r'exec\s*\(',
                r'open\s*\(',
                r'file\s*\(',
            ],
        },

        'javascript': {
            'compile_command': '',
            'run_command': 'node {file}',
            'file_extension': 'js',
            'max_execution_time': 5,
            'max_memory': 256,
            'allowed_libraries': [],
            'forbidden_patterns': [
                r'require\s*\(\s*[\'"]fs[\'"]',
                r'require\s*\(\s*[\'"]os[\'"]',
                r'require\s*\(\s*[\'"]child_process[\'"]',
                r'require\s*\(\s*[\'"]http[\'"]',
                r'require\s*\(\s*[\'"]https[\'"]',
                r'require\s*\(\s*[\'"]net[\'"]',
                r'import\s+fs',
                r'import\s+os',
                r'import\s+child_process',
                r'process\.exit',
            ],
        },

        'java': {
            'compile_command': (
                'javac -J-Xmx256m -J-XX:ReservedCodeCacheSize=32m '
                '-J-XX:MaxMetaspaceSize=128m {file}'
            ),
            'run_command': (
                'java -Xmx256m -XX:ReservedCodeCacheSize=32m '
                '-XX:MaxMetaspaceSize=128m {filename}'
            ),
            'file_extension': 'java',
            'max_execution_time': 10,
            'max_memory': 512,
            'allowed_libraries': [],
            'forbidden_patterns': [
                r'import\s+java\.io\.',
                r'import\s+java\.net\.',
                r'import\s+java\.nio\.',
                r'import\s+java\.lang\.reflect\.',
                r'import\s+java\.security\.',
                r'import\s+java\.util\.concurrent\.',
                r'System\.exit',
                r'Runtime\.getRuntime',
                r'ProcessBuilder',
            ],
        },

        'cpp': {
            'compile_command': 'g++ -std=c++17 -O2 -Wall -Wextra {file} -o {filename}',
            'run_command': './{filename}',
            'file_extension': 'cpp',
            'max_execution_time': 5,
            'max_memory': 256,
            'allowed_libraries': [
                'iostream',
                'vector',
                'string',
                'algorithm',
                'cmath'
            ],
            'forbidden_patterns': [
                r'#include\s*<fstream>',
                r'#include\s*<filesystem>',
                r'#include\s*<cstdlib>',
                r'#include\s*<unistd>',
                r'#include\s*<sys/',
                r'system\s*\(',
                r'exec\s*\(',
                r'fork\s*\(',
                r'popen\s*\(',
            ],
        },

        'c': {
            'compile_command': 'gcc -std=c11 -O2 -Wall -Wextra {file} -o {filename}',
            'run_command': './{filename}',
            'file_extension': 'c',
            'max_execution_time': 5,
            'max_memory': 256,
            'allowed_libraries': [
                'stdio.h',
                'stdlib.h',
                'string.h',
                'math.h'
            ],
            'forbidden_patterns': [
                r'#include\s*<unistd>',
                r'#include\s*<sys/',
                r'system\s*\(',
                r'exec\s*\(',
                r'fork\s*\(',
                r'popen\s*\(',
            ],
        },
    }

    MEMORY_ESTIMATES = {
        'javascript': 8,
        'python': 12,
        'java': 25,
        'cpp': 15,
        'c': 12,
    }

    def __init__(self):
        self.temp_dir = None
        self.security_configs = {}
        self._load_security_configs()

    def _load_security_configs(self):
        """Загрузка конфигураций безопасности из БД"""

        try:
            db_configs = SecurityConfig.objects.filter(is_enabled=True)

            for config in db_configs:
                self.security_configs[config.programming_language] = {
                    'compile_command': config.compile_command,
                    'run_command': config.run_command,
                    'file_extension': config.file_extension,
                    'max_execution_time': config.max_execution_time,
                    'max_memory': config.max_memory,
                    'allowed_libraries': config.allowed_libraries,
                    'forbidden_patterns': config.forbidden_patterns,
                    'security_level': config.security_level,
                }

        except Exception:
            pass

    def _create_sandbox(self) -> str:
        """Создание песочницы"""

        self.temp_dir = tempfile.mkdtemp(prefix='code_sandbox_')

        os.chmod(self.temp_dir, 0o700)

        work_dir = os.path.join(self.temp_dir, 'work')

        os.makedirs(work_dir, mode=0o700)

        return work_dir

    def _cleanup_sandbox(self):
        """Удаление песочницы"""

        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as error:
                pass

    def _validate_code(
        self,
        code: str,
        language: str
    ) -> Tuple[bool, List[str]]:
        """Проверка безопасности кода"""

        errors = []

        config = self.security_configs.get(
            language,
            self.DEFAULT_CONFIGS.get(language, {})
        )

        if not config:
            return False, [f"Язык {language} не поддерживается"]

        forbidden_patterns = config.get('forbidden_patterns', [])

        for pattern in forbidden_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                errors.append(
                    f"Обнаружен запрещенный паттерн: {pattern}"
                )

        return len(errors) == 0, errors

    def _set_resource_limits(self, limits: Dict):
        """Ограничения ресурсов"""

        if os.name == 'nt':

            def set_limits():
                pass

        else:
            import resource

            def set_limits():
                for limit_name, limit_value in limits.items():
                    if hasattr(resource, limit_name):
                        resource.setrlimit(
                            getattr(resource, limit_name),
                            (limit_value, limit_value)
                        )

        return set_limits

    def _execute_in_sandbox(
        self,
        command: str,
        work_dir: str,
        timeout: int,
        memory_limit: int,
        input_data: str = '',
        nofile_limit: int = None
    ) -> Dict:
        """Запуск команды"""

        try:
            command_args = shlex.split(command, posix=os.name != 'nt')

            resource_limits = {
                'RLIMIT_CPU': timeout,
                'RLIMIT_AS': memory_limit * 1024 * 1024,
                'RLIMIT_FSIZE': 10 * 1024 * 1024,
                'RLIMIT_NOFILE': nofile_limit or self.NOFILE_LIMIT,
            }

            if os.name == 'nt':

                process = subprocess.Popen(
                    command_args,
                    shell=False,
                    cwd=work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )

            else:

                process = subprocess.Popen(
                    command_args,
                    shell=False,
                    cwd=work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    preexec_fn=self._set_resource_limits(
                        resource_limits
                    )
                )

            start_time = time.time()

            try:
                stdout, stderr = process.communicate(
                    input=input_data,
                    timeout=timeout
                )

                execution_time = round(
                    time.time() - start_time,
                    3
                )

                success = process.returncode == 0

                return {
                    'success': success,
                    'stdout': stdout.strip(),
                    'stderr': stderr.strip(),
                    'return_code': process.returncode,
                    'execution_time': execution_time,
                    'timeout': False,
                }

            except subprocess.TimeoutExpired:

                process.kill()
                process.wait()

                return {
                    'success': False,
                    'stdout': '',
                    'stderr': 'Превышен лимит времени выполнения',
                    'return_code': -1,
                    'execution_time': timeout,
                    'timeout': True,
                }

        except Exception as error:

            return {
                'success': False,
                'stdout': '',
                'stderr': f'Ошибка выполнения: {str(error)}',
                'return_code': -1,
                'execution_time': 0,
                'timeout': False,
            }

    def _normalize_command_for_runtime(self, command: str, language: str) -> str:
        try:
            command_args = shlex.split(command, posix=os.name != 'nt')
        except ValueError:
            return command

        if language == 'python' and command_args and command_args[0].lower() in {'python', 'python3', 'py'}:
            command_args[0] = sys.executable
            if os.name == 'nt':
                return subprocess.list2cmdline(command_args)
            return ' '.join(shlex.quote(part) for part in command_args)

        if os.name == 'nt' and language in {'cpp', 'c'} and command_args:
            executable = command_args[0]
            if executable.startswith('./') or executable.startswith('.\\'):
                executable = executable[2:]
            if not executable.lower().endswith('.exe'):
                executable = f'{executable}.exe'
            command_args[0] = executable
            return subprocess.list2cmdline(command_args)

        return command

    def _source_filename_for_language(
        self,
        code: str,
        language: str,
        file_extension: str
    ) -> str:
        if language != 'java':
            return f'solution.{file_extension}'

        public_class = re.search(
            r'\bpublic\s+class\s+([A-Za-z_][A-Za-z0-9_]*)',
            code
        )
        if public_class:
            return f'{public_class.group(1)}.{file_extension}'

        main_class = re.search(
            r'\bclass\s+Main\b',
            code
        )
        if main_class:
            return f'Main.{file_extension}'

        return f'Solution.{file_extension}'

    def _effective_memory_limit(
        self,
        language: str,
        memory_limit: int,
        is_compile: bool = False
    ) -> int:
        minimums = (
            self.MIN_COMPILE_MEMORY_MB
            if is_compile
            else self.MIN_RUNTIME_MEMORY_MB
        )
        return max(memory_limit, minimums.get(language, memory_limit))

    def _parse_javascript_error(self, stderr: str) -> str:
        """Красивый вывод ошибок JavaScript"""

        if not stderr:
            return 'Неизвестная ошибка JavaScript'

        lines = stderr.strip().split('\n')

        formatted = []

        for line in lines:

            clean_line = line.strip()

            if not clean_line:
                continue

            if (
                'ReferenceError' in clean_line or
                'SyntaxError' in clean_line or
                'TypeError' in clean_line or
                'Error:' in clean_line
            ):
                formatted.append(f'Ошибка: {clean_line}')

            elif 'at ' in clean_line and '.js:' in clean_line:
                formatted.append(f'Строка: {clean_line}')

        return '\n'.join(formatted) if formatted else stderr

    def _parse_python_error(self, stderr: str) -> str:
        """Красивый вывод ошибок Python"""

        if not stderr:
            return 'Неизвестная ошибка Python'

        lines = stderr.strip().split('\n')

        formatted = []

        for line in lines:

            clean_line = line.strip()

            if not clean_line:
                continue

            if clean_line.startswith('Traceback'):
                formatted.append(clean_line)

            elif 'File "' in clean_line:
                formatted.append(f'Строка: {clean_line}')

            elif (
                'SyntaxError' in clean_line or
                'NameError' in clean_line or
                'TypeError' in clean_line or
                'ValueError' in clean_line
            ):
                formatted.append(f'Ошибка: {clean_line}')

        return '\n'.join(formatted) if formatted else stderr

    def _parse_java_error(self, stderr: str) -> str:
        """Красивый вывод ошибок Java"""

        if not stderr:
            return 'Неизвестная ошибка Java'

        lines = stderr.strip().split('\n')

        formatted = []

        for line in lines:

            clean_line = line.strip()

            if not clean_line:
                continue

            if '.java:' in clean_line:
                formatted.append(f'Строка: {clean_line}')

            elif (
                'error:' in clean_line or
                'Exception' in clean_line
            ):
                formatted.append(f'Ошибка: {clean_line}')

        return '\n'.join(formatted) if formatted else stderr

    def _parse_cpp_error(self, stderr: str) -> str:
        """Красивый вывод ошибок C/C++"""

        if not stderr:
            return 'Неизвестная ошибка C/C++'

        lines = stderr.strip().split('\n')

        formatted = []

        for line in lines:

            clean_line = line.strip()

            if not clean_line:
                continue

            if '.cpp:' in clean_line or '.c:' in clean_line:
                formatted.append(f'Строка: {clean_line}')

            elif 'error:' in clean_line:
                formatted.append(f'Ошибка: {clean_line}')

            elif 'warning:' in clean_line:
                formatted.append(f'Предупреждение: {clean_line}')

        return '\n'.join(formatted) if formatted else stderr

    def compile_and_run(
        self,
        code: str,
        language: str,
        input_data: str = "",
        timeout: int = None,
        memory_limit: int = None
    ) -> Dict:
        """Компиляция и запуск кода"""

        work_dir = None

        try:
            is_valid, errors = self._validate_code(
                code,
                language
            )

            if not is_valid:
                return {
                    'success': False,
                    'error': 'Код не прошел проверку безопасности',
                    'security_errors': errors,
                    'status': 'error',
                    'stdout': '',
                    'stderr': '\n'.join(errors),
                    'return_code': -1,
                    'execution_time': 0,
                    'timeout': False,
                    'memory_used': 0,
                }

            config = self.security_configs.get(
                language,
                self.DEFAULT_CONFIGS.get(language, {})
            )

            if not config:
                return {
                    'success': False,
                    'error': f'Язык {language} не поддерживается',
                    'status': 'error',
                    'stdout': '',
                    'stderr': '',
                    'return_code': -1,
                    'execution_time': 0,
                    'timeout': False,
                    'memory_used': 0,
                }

            work_dir = self._create_sandbox()

            timeout = timeout or config.get(
                'max_execution_time',
                5
            )

            memory_limit = memory_limit or config.get(
                'max_memory',
                256
            )
            runtime_memory_limit = self._effective_memory_limit(
                language,
                memory_limit,
                is_compile=False
            )
            compile_memory_limit = self._effective_memory_limit(
                language,
                runtime_memory_limit,
                is_compile=True
            )

            file_extension = config.get(
                'file_extension',
                'txt'
            )

            filename = self._source_filename_for_language(
                code,
                language,
                file_extension
            )

            filepath = os.path.join(
                work_dir,
                filename
            )

            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(code)

            compile_command = config.get(
                'compile_command',
                ''
            )

            if compile_command:

                compile_command = compile_command.format(
                    file=filename,
                    filename=filename.replace(
                        f'.{file_extension}',
                        ''
                    )
                )

                compile_result = self._execute_in_sandbox(
                    compile_command,
                    work_dir,
                    timeout,
                    compile_memory_limit,
                    nofile_limit=self.NOFILE_LIMIT
                )

                if compile_result['return_code'] != 0:
                    compile_error = (
                        compile_result['stderr'] or
                        compile_result['stdout'] or
                        f"Компилятор завершился с кодом {compile_result['return_code']}"
                    )

                    return {
                        'success': False,
                        'error': 'Ошибка компиляции',
                        'compile_output': compile_error,
                        'status': 'error',
                        'stdout': '',
                        'stderr': compile_error,
                        'return_code': compile_result['return_code'],
                        'execution_time': compile_result['execution_time'],
                        'timeout': compile_result['timeout'],
                        'memory_used': self.MEMORY_ESTIMATES.get(
                            language.lower(),
                            10
                        ),
                    }

            run_command = config.get(
                'run_command',
                ''
            )

            run_command = run_command.format(
                file=filename,
                filename=filename.replace(
                    f'.{file_extension}',
                    ''
                )
            )
            run_command = self._normalize_command_for_runtime(
                run_command,
                language
            )

            result = self._execute_in_sandbox(
                run_command,
                work_dir,
                timeout,
                runtime_memory_limit,
                input_data=input_data,
                nofile_limit=self.NOFILE_LIMIT
            )

            status = 'success'
            error_message = ''

            if result['timeout']:

                status = 'timeout'
                error_message = (
                    'Превышен лимит времени выполнения'
                )

            elif result['return_code'] != 0:

                status = 'error'

                if language == 'javascript':
                    error_message = self._parse_javascript_error(
                        result['stderr']
                    )

                elif language == 'python':
                    error_message = self._parse_python_error(
                        result['stderr']
                    )

                elif language == 'java':
                    error_message = self._parse_java_error(
                        result['stderr']
                    )

                elif language in ['cpp', 'c']:
                    error_message = self._parse_cpp_error(
                        result['stderr']
                    )

                else:
                    error_message = result['stderr']

            return {
                'success': result['return_code'] == 0,
                'stdout': result['stdout'],
                'stderr': error_message,
                'execution_time': result['execution_time'],
                'timeout': result['timeout'],
                'return_code': result['return_code'],
                'status': status,
                'memory_used': self.MEMORY_ESTIMATES.get(
                    language.lower(),
                    10
                ),
                'error_details': (
                    error_message
                    if status == 'error'
                    else None
                ),
            }

        except Exception as exception:

            return {
                'success': False,
                'error': f'Внутренняя ошибка: {str(exception)}',
                'status': 'error',
                'stdout': '',
                'stderr': f'Внутренняя ошибка: {str(exception)}',
                'return_code': -1,
                'execution_time': 0,
                'timeout': False,
                'memory_used': 0,
            }

        finally:

            if work_dir:
                self._cleanup_sandbox()

    def run_test_cases(
        self,
        code: str,
        language: str,
        test_cases: List[Dict]
    ) -> Dict:
        """Запуск тестов"""

        results = {
            'total_tests': len(test_cases),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': [],
            'overall_status': 'wrong'
        }

        for index, test_case in enumerate(test_cases):

            expected_output = (
                test_case.get(
                    'expected_output',
                    ''
                ).strip()
            )

            timeout = test_case.get('timeout', 5)

            result = self.compile_and_run(
                code,
                language,
                '',
                timeout
            )

            actual_output = result.get(
                'stdout',
                ''
            ).strip()

            normalized_actual = '\n'.join(
                line.rstrip() for line in actual_output.splitlines()
            ).strip()
            normalized_expected = '\n'.join(
                line.rstrip() for line in expected_output.splitlines()
            ).strip()

            test_passed = (
                normalized_actual == normalized_expected and
                result.get('success', False)
            )

            test_result = {
                'test_number': index + 1,
                'input': '',
                'expected_output': expected_output,
                'actual_output': actual_output,
                'passed': test_passed,
                'execution_time': result.get(
                    'execution_time',
                    0
                ),
                'status': result.get(
                    'status',
                    'error'
                ),
                'error': result.get(
                    'stderr',
                    ''
                ),
            }

            results['test_results'].append(
                test_result
            )

            if test_passed:
                results['passed_tests'] += 1
            else:
                results['failed_tests'] += 1

        if results['passed_tests'] > 0:
            results['overall_status'] = 'success'
        elif any(item.get('status') == 'error' for item in results['test_results']):
            results['overall_status'] = 'error'

        return results


compiler = CodeCompiler()
