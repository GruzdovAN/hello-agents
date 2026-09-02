import os
import json
import zipfile
import subprocess
import shutil
from typing import Dict, Any, List

from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import Tool, ToolParameter, ToolResponse
from hello_agents.tools.response import ToolStatus

class UserMemoryTool(Tool):
    """Инструмент управления памятью об уровне пользователя"""

    def __init__(self, memory_file: str = "user_memory.json"):
        super().__init__(
            name="user_memory",
            description="Получить или обновить уровень программирования пользователя и историю задач"
        )
        self.memory_file = os.path.join(os.path.dirname(__file__), "../../data", memory_file)
        self._ensure_memory_file()

    def _ensure_memory_file(self):
        if not os.path.exists(self.memory_file):
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump({"level": "beginner", "history": []}, f)

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        action = parameters.get("action")
        
        with open(self.memory_file, "r", encoding="utf-8") as f:
            memory = json.load(f)

        if action == "get":
            return ToolResponse.success(text=json.dumps(memory, ensure_ascii=False))
        elif action == "update":
            new_level = parameters.get("level")
            new_record = parameters.get("record")
            if new_level:
                memory["level"] = new_level
            if new_record:
                memory["history"].append(new_record)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            return ToolResponse.success(text="Память обновлена успешно")
        else:
            return ToolResponse.error(text="Недопустимое действие action")

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="action",
                type="string",
                description="Тип операции: 'get' или 'update'",
                required=True
            ),
            ToolParameter(
                name="level",
                type="string",
                description="Новая оценка уровня пользователя (например 'beginner', 'intermediate', 'advanced')",
                required=False
            ),
            ToolParameter(
                name="record",
                type="string",
                description="Запись о выполненной задаче",
                required=False
            )
        ]

class CodeTestTool(Tool):
    """Инструмент автоматического тестирования и оценки кода"""

    def __init__(self):
        super().__init__(
            name="code_test",
            description="Распаковать загруженный архив проекта, запустить тесты и выставить оценку"
        )
        self.extract_dir = os.path.join(os.path.dirname(__file__), "../../outputs/extracted")

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        zip_path = parameters.get("zip_path")
        test_code = parameters.get("test_code")
        
        if not zip_path or not os.path.exists(zip_path):
            return ToolResponse.error(text="Ошибка: путь к архиву не существует")
            
        if not test_code:
            return ToolResponse.error(text="Ошибка: отсутствует тестовый код")

        if os.path.exists(self.extract_dir):
            shutil.rmtree(self.extract_dir)
        os.makedirs(self.extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_dir)
        except Exception as e:
            return ToolResponse.error(text=f"Ошибка распаковки: {str(e)}")

        test_file_path = os.path.join(self.extract_dir, "test_generated.py")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        try:
            result = subprocess.run(
                ["pytest", test_file_path, "-v"],
                cwd=self.extract_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + "\n" + result.stderr
            score = 100 if result.returncode == 0 else 0
            
            return ToolResponse.success(
                text=json.dumps({
                    "score": score,
                    "test_output": output,
                    "status": "success" if result.returncode == 0 else "failed"
                }, ensure_ascii=False)
            )
            
        except subprocess.TimeoutExpired:
            return ToolResponse.error(text="Превышено время выполнения тестов")
        except Exception as e:
            return ToolResponse.error(text=f"Ошибка выполнения тестов: {str(e)}")

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="zip_path",
                type="string",
                description="Абсолютный путь к загруженному архиву проекта",
                required=True
            ),
            ToolParameter(
                name="test_code",
                type="string",
                description="Тестовый код pytest для проверки кода пользователя",
                required=True
            )
        ]

def get_helper_agent() -> SimpleAgent:
    """Инициализировать и вернуть агента-помощника по обучению"""
    tool_registry = ToolRegistry()
    tool_registry.register_tool(UserMemoryTool())
    tool_registry.register_tool(CodeTestTool())

    model_id = os.environ.get("LLM_MODEL_ID", "Qwen/Qwen2.5-72B-Instruct")
    llm = HelloAgentsLLM(model=model_id)

    system_prompt = """Ты профессиональный помощник по изучению разработки ПО. Твои обязанности:
1. Использовать инструмент user_memory, чтобы узнать текущий уровень программирования пользователя и историю задач.
2. По уровню пользователя предлагать подходящие задачи по программированию или искать реальные кейсы из практики.
3. В процессе разработки давать целенаправленные советы и рекомендации.
4. Когда пользователь завершит разработку и загрузит архив проекта:
   - Внимательно проанализировать требования задачи.
   - Написать строгий тестовый код pytest. Важно: код пользователя обычно находится в подпапке распакованного каталога (например `test-projects/main.py`), тестовый код должен рекурсивно искать `.py` файлы и динамически импортировать модули, а не предполагать, что код лежит в текущей директории. Можно использовать `sys.path.insert(0, str(project_root))` для импорта.
   - Использовать инструмент code_test с путём к архиву и тестовым кодом для автоматической проверки проекта.
   - По результатам тестов выставить итоговую оценку и дать подробный код-ревью.
5. После завершения задачи обновить оценку уровня пользователя и историю через user_memory.

Всегда сохраняй ободряющий и профессиональный тон."""

    from hello_agents.core.config import Config
    
    config = Config(todowrite_enabled=False)

    return SimpleAgent(
        name="SoftwareDevHelper",
        llm=llm,
        system_prompt=system_prompt,
        tool_registry=tool_registry,
        config=config
    )
