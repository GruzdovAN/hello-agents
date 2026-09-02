
import io
import contextlib
from hello_agents.tools import Tool
from typing import Dict, Any

class CodeRunner(Tool):
    """
    Безопасное выполнение Python-кода и возврат вывода.
    Внимание: использует exec(); в продакшене небезопасно.
    Для реального продукта используйте sandbox (например Docker).
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
            return "Ошибка: код не предоставлен."

        # Перехват stdout и stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
                # Ограничённая глобальная область
                safe_globals = {
                    "__builtins__": __builtins__,
                    "print": print,
                    "range": range,
                    "len": len,
                    # при необходимости добавьте другие безопасные встроенные функции
                }
                exec(code, safe_globals)
            
            output = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()
            
            result = ""
            if output:
                result += f"Вывод:\n{output}\n"
            if errors:
                result += f"Ошибки:\n{errors}\n"
            
            if not result:
                result = "Код выполнен успешно, вывод пуст."
                
            return result

        except Exception as e:
            return f"Ошибка выполнения: {str(e)}"
