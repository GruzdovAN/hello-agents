"""Безопасный shell"""

import subprocess
import re
import os
from typing import List, Dict, Any

from hello_agents.tools import Tool, ToolParameter, ToolResponse, tool_action


# Команды белого списка (разрешены только эти основные команды)

ALLOWED_COMMANDS = [
    "ls", "cat", "echo", "pwd", "git", "npm", "pnpm", "uv", "python",
    "python3", "node", "yarn", "pip", "pip3", "mkdir", "touch", "cp",
    "mv", "grep", "find", "head", "tail", "wc", "sort", "uniq",
]

# Опасные шаблоны команд (регулярные выражения)

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",           # Рекурсивное принудительное удаление

    r"rm\s+-fr",           # Рекурсивное принудительное удаление (вариант)

    r"sudo",               # Команда повышения привилегий

    r"chmod\s+777",        # Опасные настройки разрешений

    r">\s*/dev/",          # Записать файл устройства

    r"mkfs",               # команда форматирования

    r"dd\s+if=",           # копия диска

    r">\s*/etc/",          # Написать конфигурацию системы

    r"shutdown",           # команда выключения

    r"reboot",             # Команда перезапуска

    r"init\s+[06]",        # Переключить уровень запуска

    r"kill\s+-9\s+1",      # Убейте процесс инициализации

    r":(){ :\|:& };:",     # Вилочная бомба

    r">\s*\$HOME",         # Перезаписать каталог пользователя

    r">\s*~",              # Перезаписать каталог пользователя

]


class ExecuteCommandTool(Tool):
    """инструмент выполнения команд

    Обеспечивает возможности безопасного выполнения команд оболочки, в том числе:
    - Механизм белого списка команд
    - Опасный перехват команд
    - ограничения рабочего каталога
    - Контроль тайм-аута выполнения"""

    def __init__(
        self,
        allowed_commands: List[str] = None,
        dangerous_patterns: List[str] = None,
        max_output_size: int = 10000,
        timeout: int = 30,
        allowed_directories: List[str] = None,
    ):
        """Инициализировать инструмент выполнения команд

        Аргументы:
            разрешенные_команды: список разрешенных команд, ALLOWED_COMMANDS используется по умолчанию.
            Опасные_паттерны: список опасных шаблонов команд, по умолчанию используются ОПАСНЫЕ_ШАБЛОНЫ.
            max_output_size: Максимальный размер вывода (символов), по умолчанию 10 000.
            timeout: тайм-аут выполнения команды (секунды), по умолчанию 30
            разрешенные_каталоги: список разрешенных рабочих каталогов, «Нет» означает отсутствие ограничений."""
        super().__init__(
            name="execute_command",
            description="Безопасное выполнение shell-команд с белым списком и блокировкой опасных команд",
            expandable=True
        )

        self.allowed_commands = allowed_commands or ALLOWED_COMMANDS
        self.dangerous_patterns = dangerous_patterns or DANGEROUS_PATTERNS
        self.max_output_size = max_output_size
        self.timeout = timeout
        self.allowed_directories = allowed_directories

        # Компиляция регулярных выражений опасных шаблонов

        self._dangerous_regex = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns
        ]

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Выполнить команду (поведение по умолчанию)"""
        command = parameters.get("command", "")
        workdir = parameters.get("workdir")
        return self._execute_command(command, workdir)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                type="string",
                description="Shell-команда для выполнения",
                required=True
            ),
            ToolParameter(
                name="workdir",
                type="string",
                description="Рабочий каталог (опционально)",
                required=False
            ),
        ]

    def _validate_command(self, command: str) -> tuple[bool, str]:
        """Убедитесь, что команда безопасна

        Аргументы:
            команда: команда для проверки

        Возврат:
            (is_safe, причина): безопасно ли это, причина, по которой это небезопасно"""
        # Проверьте наличие опасных шаблонов

        for pattern in self._dangerous_regex:
            if pattern.search(command):
                return False, f"Команда содержит опасный шаблон: {pattern.pattern}"

        # Извлеките базовую команду (первое слово командной строки)

        # Команды обработки с путями (например, /usr/bin/ls)

        command_parts = command.strip().split()
        if not command_parts:
            return False, "Пустая команда"

        base_cmd = os.path.basename(command_parts[0])

        # Проверить белый список

        if base_cmd not in self.allowed_commands:
            return False, f"Команда '{base_cmd}' не в белом списке. Разрешённые: {', '.join(self.allowed_commands[:10])}..."

        return True, ""

    def _validate_workdir(self, workdir: str) -> tuple[bool, str]:
        """Проверить рабочий каталог

        Аргументы:
            workdir: путь к рабочему каталогу

        Возврат:
            (is_valid, причина): действителен ли он, причина недействительности"""
        # Если разрешенные_каталоги не установлены, разрешены все каталоги.

        if not self.allowed_directories:
            return True, ""

        # Проверьте, находится ли каталог в списке разрешенных

        abs_workdir = os.path.abspath(workdir)
        for allowed_dir in self.allowed_directories:
            abs_allowed = os.path.abspath(allowed_dir)
            if abs_workdir.startswith(abs_allowed):
                return True, ""

        return False, f"Каталог '{workdir}' не в списке разрешённых"

    def _execute_command(
        self,
        command: str,
        workdir: str = None,
        timeout: int = None,
    ) -> ToolResponse:
        """Базовая реализация выполнения команд

        Аргументы:
            команда: команда, которая будет выполнена
            рабочий каталог: рабочий каталог
            тайм-аут: тайм-аут (секунды)

        Возврат:
            ToolResponse: результат выполнения"""
        if not command:
            return ToolResponse.error(
                code="INVALID_INPUT",
                message="Команда не может быть пустой"
            )

        # Проверьте безопасность команд

        is_safe, reason = self._validate_command(command)
        if not is_safe:
            return ToolResponse.error(
                code="COMMAND_BLOCKED",
                message=f"Команда заблокирована: {reason}"
            )

        # Проверьте рабочий каталог

        if workdir:
            is_valid, reason = self._validate_workdir(workdir)
            if not is_valid:
                return ToolResponse.error(
                    code="DIRECTORY_NOT_ALLOWED",
                    message=f"Недопустимый рабочий каталог: {reason}"
                )

        # выполнить команду

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=timeout or self.timeout,
            )

            # Обрезать слишком длинный вывод

            stdout = result.stdout
            stderr = result.stderr

            if len(stdout) > self.max_output_size:
                stdout = stdout[:self.max_output_size] + f"\n... (вывод обрезан, всего {len(result.stdout)} символов)"
            if len(stderr) > self.max_output_size:
                stderr = stderr[:self.max_output_size] + f"\n... (stderr обрезан, всего {len(result.stderr)} символов)"

            # Построить ответ

            output_parts = []
            if stdout:
                output_parts.append(f"Вывод:\n{stdout}")
            if stderr:
                output_parts.append(f"Ошибка:\n{stderr}")

            output_text = "\n\n".join(output_parts) if output_parts else "Команда выполнена (нет вывода)"

            return ToolResponse.success(
                text=output_text,
                data={
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "command": command,
                    "workdir": workdir,
                }
            )

        except subprocess.TimeoutExpired:
            return ToolResponse.error(
                code="TIMEOUT",
                message=f"Таймаут выполнения ({timeout or self.timeout} с)"
            )
        except Exception as e:
            return ToolResponse.error(
                code="EXECUTION_ERROR",
                message=f"Ошибка выполнения: {str(e)}"
            )

    @tool_action("exec_run", "Выполнить shell-команду")
    def _run_command(
        self,
        command: str,
        workdir: str = None,
        timeout: int = None,
    ) -> str:
        """Выполнить команду оболочки

        Аргументы:
            команда: команда, которая будет выполнена
            рабочий каталог: рабочий каталог (необязательно)
            timeout: тайм-аут (секунды, необязательно)"""
        response = self._execute_command(command, workdir, timeout)
        return response.text

    @tool_action("exec_allowed_commands", "Список разрешённых команд")
    def _list_allowed_commands(self) -> str:
        """Список всех разрешенных команд"""
        return "Разрешённые команды:\n" + "\n".join(f"- {cmd}" for cmd in sorted(self.allowed_commands))

    @tool_action("exec_dangerous_patterns", "Список опасных шаблонов команд")
    def _list_dangerous_patterns(self) -> str:
        """Перечислите все опасные шаблоны команд, которые будут заблокированы"""
        return "Опасные шаблоны команд:\n" + "\n".join(f"- {pattern}" for pattern in self.dangerous_patterns)
