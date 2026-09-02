"""TerminalTool — инструмент командной строки

Безопасное выполнение команд для агента (Agent):
- файловая система (ls, cat, head, tail, find, grep)
- текст (wc, sort, uniq)
- каталоги (pwd, cd)
- whitelist, sandbox путей, таймаут

Сценарии использования:
- JIT-чтение и анализ файлов
- исследование репозитория
- анализ логов
- предпросмотр данных

Безопасность:
- whitelist безопасных команд
- sandbox рабочего каталога
- таймаут
- лимит вывода
- запрет rm, mv, chmod и т.д.
"""

from typing import Dict, Any, List, Optional
import subprocess
import os
from pathlib import Path
import shlex
import re

from ..base import Tool, ToolParameter


class TerminalTool(Tool):
    """Инструмент командной строки
    
    Безопасное выполнение типовых команд ФС и текста.
    
    Ограничения:
    - только whitelist
    - только workspace
    - таймаут (30 с по умолчанию)
    - лимит вывода (10 МБ)
    
    Пример использования:
    ```python
    terminal = TerminalTool(workspace="./project")
    
    # список файлов
    result = terminal.run({"command": "ls -la"})
    
    # содержимое файла
    result = terminal.run({"command": "cat README.md"})
    
    # поиск
    result = terminal.run({"command": "grep -r 'TODO' src/"})
    
    # первые 10 строк
    result = terminal.run({"command": "head -n 10 data.csv"})
    ```
    """
    
    # Whitelist команд
    # Безопасные команды для чтения и анализа
    # Без rm/mv/chmod и т.п.
    ALLOWED_COMMANDS = {
        # Список и метаданные
        'ls', 'dir', 'tree',
        # Просмотр содержимого
        'cat', 'head', 'tail', 'less', 'more',
        # Поиск
        'find', 'grep', 'egrep', 'fgrep', 'rg',
        # Обработка текста
        'wc', 'sort', 'uniq', 'cut', 'awk', 'sed',
        # Shell builtins (пайпы; общие ограничения)
        'echo', 'printf',
        # mkdir в sandbox
        'mkdir',
        # Каталоги
        'pwd', 'cd',
        # Метаданные файлов
        'file', 'stat', 'du', 'df',
        # Прочее
        'which', 'whereis',
        # git: только безопасные подкоманды
        'git',
    }

    # Shell-метасимволы (комбинации, запись, подкоманды)
    # Метасимволы shell — комбинации и опасные операции
    # Проверка по политике безопасности
    SHELL_META_TOKENS = ["|", "||", "&&", ";", ">", ">>", "<", "$(", "`"]

    # Опасные команды — распознавание; решение на верхнем уровне
    # необратимые изменения без allow_dangerous
    DANGEROUS_BASE_COMMANDS = {"rm", "chmod"}
    # Опасные подкоманды git
    DANGEROUS_GIT_SUBCOMMANDS = {("reset", "--hard"), ("reset", "--hard", "HEAD")}
    
    def __init__(
        self,
        workspace: str = ".",
        timeout: int = 30,
        max_output_size: int = 10 * 1024 * 1024,  # 10MB
        allow_cd: bool = True,
        confirm_dangerous: bool = False,
        default_shell_mode: bool = False,
    ):
        """Инициализация TerminalTool
        
        Args:
            workspace: workspace — все команды только внутри
            timeout: таймаут (с)
            max_output_size: лимит вывода (байты)
            allow_cd: разрешить cd
            confirm_dangerous: confirm_dangerous
            default_shell_mode: default_shell_mode
        """
        super().__init__(
            name="terminal",
            description="Терминал — безопасные команды ФС и текста (ls, cat, grep, head, tail и др.)"
        )
        
        # resolve workspace
        self.workspace = Path(workspace).resolve()
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.allow_cd = allow_cd
        self.confirm_dangerous = confirm_dangerous
        self.default_shell_mode = default_shell_mode
        
        # cwd относительно workspace
        # старт в корне workspace
        self.current_dir = self.workspace
        
        # mkdir workspace при необходимости
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """Главная точка входа run()
        
Разбор и выполнение команды с полным циклом проверок:
        1. Проверка параметров
        2. Разбор команды
        3. Проверки безопасности
        4. Выполнение и результат
        
Механизмы безопасности:
        - whitelist команд
        - sandbox путей
        - подтверждение опасных команд
        - таймаут
        - лимит вывода
        
        Args:
            parameters: command, allow_dangerous, shell_mode
                - command: строка команды
                - allow_dangerous: allow_dangerous
                - shell_mode: shell_mode
            
        Returns:
            str: результат или ошибка
        """
        # 1. validate
        if not self.validate_parameters(parameters):
            return "❌ Ошибка проверки параметров"
        
        # извлечение command
        command = parameters.get("command", "").strip()
        allow_dangerous = bool(parameters.get("allow_dangerous", False))
        shell_mode = bool(parameters.get("shell_mode", self.default_shell_mode))
        
        # пустая команда
        if not command:
            return "❌ Команда не может быть пустой"

        # shell vs argv
        # shell: пайпы, строже проверки
        # argv: без shell
        if shell_mode:
            return self._execute_shell(command, allow_dangerous=allow_dangerous)
        
        # 2. shlex.split
        try:
            parts = shlex.split(command)
        except ValueError as e:
            return f"❌ Ошибка разбора команды: {e}"
        
        # повторная проверка
        if not parts:
            return "❌ Команда не может быть пустой"
        
        base_command = parts[0]
        
        # 3. whitelist
        # первая линия защиты
        if base_command not in self.ALLOWED_COMMANDS:
            return f"❌ Команда не разрешена: {base_command}\nРазрешённые команды: {', '.join(sorted(self.ALLOWED_COMMANDS))}"

        # git: проверка подкоманд
        if base_command == "git":
            return self._handle_git(parts, allow_dangerous)

        # 4. confirm dangerous
        # интерактивное подтверждение
        # последняя линия подтверждения
        if allow_dangerous and self.confirm_dangerous:
            ans = input(f"\n⚠️ Рискованная команда: {command}\nРазрешить? (y/n)\nconfirm> ").strip().lower()
            if ans not in {"y", "yes"}:
                return "⛔️ Отменено (нет подтверждения)."

        # cd отдельно
        if base_command == 'cd':
            return self._handle_cd(parts)
        
        # 5. execute
        return self._execute_argv(parts, allow_dangerous=allow_dangerous)
    
    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        return [
            ToolParameter(
                name="command",
                type="string",
                description=(
                    f"Команда (whitelist: {', '.join(sorted(list(self.ALLOWED_COMMANDS)[:10]))}...）\n"
                    "Примеры: 'ls -la', 'cat file.txt', 'grep pattern *.py', 'head -n 20 data.csv'"
                ),
                required=True
            ),
            ToolParameter(
                name="allow_dangerous",
                type="boolean",
                description="allow_dangerous (по умолчанию false)",
                required=False
            ),
            ToolParameter(
                name="shell_mode",
                type="boolean",
                description="shell_mode (пайпы/редиректы; по умолчанию из конфига)",
                required=False,
            ),
        ]

    def _contains_shell_meta(self, command: str) -> bool:
        """Проверка shell-метасимволов
        
        Args:
            command: команда
            
        Returns:
            bool: True если есть метасимволы
        """
        return any(tok in command for tok in self.SHELL_META_TOKENS)

    # --- shell parsing helpers (ignore operators inside quotes) ---
    def _split_shell_segments(self, command: str) -> List[str]:
        """
        Разделение по | && ; вне кавычек.
        Сегменты без операторов.
        
        Анализ сложных shell-команд.
        
        Args:
            command: shell-команда
            
        Returns:
            List[str]: список сегментов
        """
        ops = ["||", "&&", "|", ";"]
        segs: List[str] = []
        buf: List[str] = []
        i = 0
        quote: Optional[str] = None
        while i < len(command):
            ch = command[i]
            if ch in {"'", '"'}:
                if quote is None:
                    quote = ch
                elif quote == ch:
                    quote = None
                buf.append(ch)
                i += 1
                continue
            if ch == "\\":
                buf.append(ch)
                if i + 1 < len(command):
                    buf.append(command[i + 1])
                    i += 2
                else:
                    i += 1
                continue
            if quote is None:
                matched = False
                for op in ops:
                    if command.startswith(op, i):
                        seg = "".join(buf).strip()
                        if seg:
                            segs.append(seg)
                        buf = []
                        i += len(op)
                        matched = True
                        break
                if matched:
                    continue
            buf.append(ch)
            i += 1
        seg = "".join(buf).strip()
        if seg:
            segs.append(seg)
        return segs

    def _has_unquoted(self, command: str, token: str) -> bool:
        """token вне кавычек?
        
        Детекция опасных shell-операторов,
        вне кавычек — риск.
        
        Args:
            command: команда
            token: token
            
        Returns:
            bool: True если token вне кавычек
        """
        q: Optional[str] = None
        i = 0
        while i < len(command):
            ch = command[i]
            if ch in {"'", '"'}:
                if q is None:
                    q = ch
                elif q == ch:
                    q = None
                i += 1
                continue
            if ch == "\\":
                i += 2
                continue
            if q is None and command.startswith(token, i):
                return True
            i += 1
        return False

    def _shell_requires_allow_dangerous(self, command: str) -> bool:
        """Нужен ли allow_dangerous?
        
        Анализ рискованных операций в shell.
        Часть модели безопасности.
        
        Проверки:
        1. > >> кроме /dev/null
        2. подстановка команд
        3. rm, chmod
        4. git reset --hard
        
        Args:
            command: shell-команда
            
        Returns:
            bool: True если нужен allow_dangerous
            
        Note:
            - не блокирует, только помечает
            - проверка при execute
            - /dev/null допускается
        """
        # > и $() — риск; /dev/null — ок
        # редирект не в /dev/null — запись
        if self._has_unquoted(command, ">") or self._has_unquoted(command, ">>"):
            # /dev/null — безопасно
            if re.search(r">\s*/dev/null", command) or re.search(r">>\s*/dev/null", command):
                pass
            else:
                # иначе — allow_dangerous
                return True
        
        # ` и $(
        # инъекция кода
        if self._has_unquoted(command, "$(") or self._has_unquoted(command, "`"):
            return True
        
        # DANGEROUS_BASE_COMMANDS
        # необратимые эффекты
        if re.search(r"(^|\s)rm(\s|$)", command):
            return True
        if re.search(r"(^|\s)chmod(\s|$)", command):
            return True
        
        # опасные git
        # reset --hard
        if re.search(r"git\s+reset\s+--hard", command):
            return True
        
        # иначе False
        return False

    def _shell_all_commands_whitelisted(self, command: str) -> bool:
        """
        Статическая проверка whitelist по сегментам
        
        Каждый сегмент — первый токен в whitelist.
        Предпроверка без allow_dangerous.
        
        Стратегия:
        1. сегменты по метасимволам
        2. base команда сегмента
        3. в whitelist?
        4. git: status/diff
        
        Args:
            command: полная shell-команда
            
        Returns:
            bool: True если все сегменты безопасны
            
        Note:
            - best-effort
            - возможны ложные срабатывания
            - git: только status/diff
        """
        # \n → пробел
        cmd = command.replace("\n", " ")
        
        # сегменты
        segments = self._split_shell_segments(cmd)
        
        # проверка каждого сегмента
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue  # пустые сегменты
                
            try:
                # shlex
                argv = shlex.split(seg)
            except Exception:
                # parse fail → unsafe
                return False
                
            if not argv:
                continue  # пустой argv
                
            # argv[0]
            base = argv[0]
            
            # whitelist base
            if base not in self.ALLOWED_COMMANDS:
                return False
                
            # git special
            # status/diff only
            if base == "git":
                if len(argv) < 2:
                    return False  # git needs subcommand
                if argv[1] not in {"status", "diff"}:
                    return False  # только status/diff
                    
        # all ok
        return True

    def _execute_shell(self, command: str, allow_dangerous: bool = False) -> str:
        """
        Выполнение shell (стиль Claude Code)
        
        Безопасный shell: пайпы, редиректы, подстановки.
        Многоуровневые проверки.
        
        Защита:
        - редирект/$()/опасное → allow_dangerous
        - без allow_dangerous → whitelist сегментов
        - confirm_dangerous для рискованного
        
        Шаги:
        1. needs_allow?
        2. whitelist
        3. confirm
        4. subprocess
        5. результат
        
        Args:
            command: shell-команда
            allow_dangerous: allow_dangerous
            
        Returns:
            str: результат
            
        Note:
            - пайпы без confirm (ls | grep)
            - confirm при записи/опасном
            - обрезка вывода
        """
        needs_allow = self._shell_requires_allow_dangerous(command)
        
        # слой 1: опасное
        # deny без allow_dangerous
        # первая линия
        if needs_allow and not allow_dangerous:
            return "❌ Запись/подстановка/риск — нужен allow_dangerous=true"

        # слой 2: whitelist
        # все сегменты в whitelist
        # только разрешённые команды
        if not allow_dangerous and not self._shell_all_commands_whitelisted(command):
            return "❌ shell_mode: команда/git вне whitelist — allow_dangerous=true"

        # Claude Code-like: pipes are allowed without confirmation; only confirm when it may write/escape/execute dangerous ops.
        if self.confirm_dangerous and (allow_dangerous or needs_allow):
            ans = input(f"\n⚠️ Рискованная shell-команда: {command}\nРазрешить? (y/n)\nconfirm> ").strip().lower()
            if ans not in {"y", "yes"}:
                return "⛔️ Отменено (нет подтверждения)."

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.current_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=os.environ.copy(),
            )

            output = (result.stdout or "") + (result.stderr or "")
            if len(output.encode("utf-8", errors="ignore")) > self.max_output_size:
                output = output[: self.max_output_size] + "\n...output truncated...\n"

            if result.returncode != 0:
                return f"Команда завершилась с кодом {result.returncode}):\n{output}"
            return output.strip() if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return f"❌ Таймаут команды (>{self.timeout}s）"
        except Exception as e:
            return f"❌ Исключение при выполнении: {e}"
    
    def _handle_cd(self, parts: List[str]) -> str:
        """Безопасный cd
        
        cd только внутри workspace.
        Абсолютные, относительные, .., ~
        
        Args:
            parts: argv cd, parts[1] — путь
            
        Returns:
            str: результат
            
        Note:
            - только внутри workspace
            - нормализация .. и .
            - запрет выхода из workspace
        """
        if not self.allow_cd:
            return "❌ cd отключён"
        
        if len(parts) < 2:
            # cd без аргументов
            return f"Текущий каталог: {self.current_dir}"
        
        target_dir = parts[1]
        
        # .. . ~
        if target_dir == "..":
            # parent
            new_dir = self.current_dir.parent
        elif target_dir == ".":
            # .
            new_dir = self.current_dir
        elif target_dir == "~":
            # ~ → workspace root
            new_dir = self.workspace
        else:
            # resolve path
            new_dir = (self.current_dir / target_dir).resolve()
        
        # relative_to workspace
        try:
            new_dir.relative_to(self.workspace)
        except ValueError:
            return f"❌ Путь вне workspace: {new_dir}"
        
        # exists?
        if not new_dir.exists():
            return f"❌ Каталог не существует: {new_dir}"
        
        # is_dir
        if not new_dir.is_dir():
            return f"❌ Не каталог: {new_dir}"
        
        # обновить cwd
        self.current_dir = new_dir
        return f"✅ Переход в: {self.current_dir}"
    
    def _execute_argv(self, argv: List[str], allow_dangerous: bool = False) -> str:
        """Выполнение argv (без shell)
        
        Прямой exec без shell — без пайпов.
        Меньше риска инъекций, меньше возможностей.
        
Проверки безопасности:
        1. confirm для rm/chmod
        2. sandbox для опасных
        3. sandbox для mkdir
        4. run + output
        
        Args:
            argv: argv
            allow_dangerous: allow_dangerous
            
        Returns:
            str: результат
            
        Note:
            - без shell-фич
            - защита от injection
            - простые команды
            - пути в workspace
        """
        # rm/chmod gate
        # DANGEROUS_BASE
        # необратимые изменения
        # первая линия
        if argv and argv[0] in self.DANGEROUS_BASE_COMMANDS and not allow_dangerous:
            return f"❌ Рискованная команда {argv[0]} нужно подтверждение (allow_dangerous=true)"

        # sandbox путей
        # пути при allow_dangerous
        # только workspace
        # anti-escape
        if argv and argv[0] in {"rm", "chmod"} and allow_dangerous:
            # каждый путь в workspace
            # относительно cwd
            for a in argv[1:]:
                if a.startswith("-"):
                    continue  # пропуск флагов
                candidate = (self.current_dir / a).resolve()
                try:
                    # relative_to
                    candidate.relative_to(self.workspace)
                except ValueError:
                    # вне workspace
                    return f"❌ Операция вне workspace: {a}"

        # mkdir sandbox
        # mkdir только в workspace
        # anti-mkdir escape
        if argv and argv[0] == "mkdir":
            for a in argv[1:]:
                if a.startswith("-"):
                    continue  # пропуск флагов
                candidate = (self.current_dir / a).resolve()
                try:
                    # candidate in workspace
                    candidate.relative_to(self.workspace)
                except ValueError:
                    # mkdir вне workspace
                    return f"❌ mkdir вне workspace: {a}"

        try:
            # subprocess argv
            # shell=False
            # capture_output
            # text=True
            result = subprocess.run(
                argv,
                shell=False,
                cwd=str(self.current_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=os.environ.copy(),
            )
            
            # stdout+stderr
            # полный вывод
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            
            # лимит размера
            if len(output) > self.max_output_size:
                output = output[:self.max_output_size]
                output += f"\n\n⚠️ Вывод обрезан (> {self.max_output_size} байт)"
            
            # returncode
            if result.returncode != 0:
                output = f"⚠️ Код возврата: {result.returncode}\n\n{output}"
            
            return output if output else "✅ Команда выполнена (нет вывода)"
            
        except subprocess.TimeoutExpired:
            # timeout
            return f"❌ Таймаут (> {self.timeout} с)"
        except Exception as e:
            # прочие исключения
            return f"❌ Ошибка выполнения: {e}"
    
    def _truncate_output(self, output: str) -> str:
        """Обрезка большого вывода
        
        Если вывод > max_output_size,
        обрезать с пометкой.
        
        Args:
            output: вывод
            
        Returns:
            str: вывод или обрезанный
            
        Note:
            - сохраняется начало
            - пометка об обрезке
        """
        if len(output) > self.max_output_size:
            return output[: self.max_output_size] + f"\n[вывод обрезан, лимит {self.max_output_size} байт]"
        return output
    
    def get_current_dir(self) -> str:
        """Текущий рабочий каталог"""
        return str(self.current_dir)
    
    def reset_dir(self):
        """Сброс cwd в корень workspace"""
        self.current_dir = self.workspace

