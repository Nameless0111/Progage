import os
import sys
from pathlib import Path

import django


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "progage.settings")
os.environ.setdefault("LOAD_ENV_LOCAL", "1")
django.setup()

from courses.compiler_service import CodeCompiler  # noqa: E402


SAMPLES = {
    "python": "print('OK')\n",
    "javascript": "console.log('OK');\n",
    "java": "public class Main { public static void main(String[] args) { System.out.println(\"OK\"); } }\n",
    "cpp": "#include <iostream>\nint main() { std::cout << \"OK\" << std::endl; return 0; }\n",
    "c": "#include <stdio.h>\nint main(void) { printf(\"OK\\n\"); return 0; }\n",
}


def main() -> int:
    compiler = CodeCompiler()
    failed = []

    print("Проверка заявленных языков выполнения кода...")

    for language, code in SAMPLES.items():
        result = compiler.compile_and_run(code, language)
        output = (result.get("stdout") or "").strip()
        ok = result.get("success") and output == "OK"
        status = "OK" if ok else "FAIL"
        print(f"{language:10} {status}")

        if not ok:
            failed.append(language)
            error = (
                result.get("stderr")
                or result.get("compile_output")
                or result.get("error")
                or result.get("error_details")
                or f"return_code={result.get('return_code')}"
            )
            if error:
                print(f"  {error}")
            if result.get("return_code") not in (None, 0):
                print(f"  return_code={result.get('return_code')}")

    if failed:
        print("\nНе найдены или не работают рантаймы:", ", ".join(failed))
        print("Обычно на Ubuntu нужны пакеты: python3 nodejs default-jdk gcc g++")
        return 1

    print("\nВсе заявленные языки работают.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
