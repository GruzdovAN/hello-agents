
import io
import contextlib
from hello_agents.tools import Tool
from typing import Dict, Any

class CodeRunner(Tool):
    """
    Инструмент для безопасного выполнения Python-кода с возвратом вывода.
    Предупреждение: этот инструмент использует exec() и небезопасен в production.
    Для реального продукта используйте песочницу, например Docker.
    """
    
    def __init__(self):
        super().__init__(
            name="code_runner",
            description="Выполняет Python-код и возвращает stdout/stderr. Вход — словарь с ключом 'code'."
        )

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Фрагмент Python-кода для выполнения"
                }
            },
            "required": ["code"]
        }

    def run(self, parameters: Dict[str, Any]) -> str:
        code = parameters.get("code", "")
        if not code:
            return "Ошибка: код не указан."

        # Перехват stdout и stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                # Создание ограниченной глобальной области видимости
                safe_globals = {
                    "__builtins__": __builtins__,
                    "print": print,
                    "range": range,
                    "len": len,
                    # При необходимости добавить другие безопасные встроенные функции
                }
                exec(code, safe_globals)
            
            output = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()
            
            result = ""
            if output:
                result += f"Вывод:\n{output}\n"
            if errors:
                result += f"Ошибка:\n{errors}\n"
            
            if not result:
                result = "Код выполнен успешно, вывода нет."
                
            return result

        except Exception as e:
            return f"Ошибка выполнения: {str(e)}"
