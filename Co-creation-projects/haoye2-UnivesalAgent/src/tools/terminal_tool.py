import subprocess
import shlex
import os

class TerminalTool:
    name = "terminal_exec"
    description = "Выполняет терминальные команды для просмотра каталогов, файлов и системной информации (поддерживаются: pwd, ls, cat, echo, whoami, date и др.)"

    def __init__(self, security_mode="strict"):
        """
        Инициализирует терминальный инструмент
        
        Args:
            security_mode: "strict" (строгий режим, немедленный отказ) или "warning" (режим предупреждений)
        """
        self.security_mode = security_mode
        
        # Расширенный белый список команд (без аргументов или с безопасными аргументами)
        self.allowed_commands = {
            "ls": [],  # ls может принимать аргументы вроде -l, -a
            "pwd": [],
            "echo": ["*"],  # echo допускает любые аргументы
            "whoami": [],
            "cat": ["*"],  # cat допускает аргументы с именами файлов
            "head": ["-n"],  # head допускает аргумент -n
            "tail": ["-n"],
            "wc": ["-l", "-w"],
            "date": [],
            "uname": ["-a"],
            "find": ["."],  # ограничиваем точку старта поиска
            # Дополнительные часто используемые безопасные команды
            "cd": [],  # смена каталога
            "mkdir": ["-p"],  # создание каталога
            "touch": [],  # создание файла
            "grep": ["-i", "-n", "-r"],  # поиск текста
            "which": [],  # поиск расположения команды
            "whereis": [],  # поиск расположения программы
            "du": ["-h", "-s"],  # использование диска
            "df": ["-h"],  # информация о файловой системе
        }
        
        # Опасные ключевые слова для дополнительной проверки безопасности
        self.dangerous_keywords = [
            "rm", "delete", "del", "format", "mkfs",
            "sudo", "su", "passwd", "chmod", "chown",
            "dd", "mkfs", "fdisk", ">", ">>", "|",
            ";", "&&", "||", "`", "$(", "eval"
        ]

    def get_parameters(self):
        return {
            "input": {
                "type": "str", 
                "description": "Введите терминальную команду, например: pwd, ls -la, cat filename.txt", 
                "required": True,
                "examples": ["pwd", "ls -la", "cat README.md", "echo hello", "whoami", "date"]
            }
        }

    def _check_command_safety(self, cmd):
        """Проверяет безопасность команды
        
        Returns:
            tuple: (is_safe, error_msg, warning_msg)
                is_safe: bool — безопасна ли команда
                error_msg: str — сообщение об ошибке
                warning_msg: str — предупреждение
        """
        # Проверка опасных ключевых слов
        cmd_lower = cmd.lower()
        for keyword in self.dangerous_keywords:
            if keyword in cmd_lower:
                error_msg = f"Обнаружена небезопасная операция: {keyword}"
                warning_msg = f"⚠️ Предупреждение: команда содержит операцию '{keyword}', что может повредить систему или привести к потере данных!"
                return False, error_msg, warning_msg
        
        # Проверка наличия конвейеров, перенаправлений и т.п.
        operators = ["|", ">", "<", "&", "&&", "||", ";"]
        for op in operators:
            if op in cmd:
                error_msg = f"Обнаружен небезопасный оператор: {op}"
                warning_msg = f"⚠️ Предупреждение: команда содержит оператор '{op}', что может привести к неожиданному поведению!"
                return False, error_msg, warning_msg
        
        return True, None, None

    def run(self, parameters):
        # Безопасная обработка параметров
        if isinstance(parameters, dict):
            # Единый формат {"input": command}
            cmd = parameters.get("input", "")
        else:
            cmd = str(parameters) if parameters else ""

        cmd = cmd.strip() if cmd else ""
        
        if not cmd:
            return "Ошибка: команда не может быть пустой"
        
        # Проверка безопасности
        is_safe, error_msg, warning_msg = self._check_command_safety(cmd)
        if not is_safe:
            if self.security_mode == "strict":
                return f"🚫 Отклонено по соображениям безопасности: {error_msg}"
            else:  # warning mode
                return f"{warning_msg}\n\nКоманда: {cmd}\n\nДля продолжения подтвердите безопасность операции.\n(Сейчас режим предупреждений, команда фактически не выполняется)"
        
        # Разделение команды и аргументов
        parts = shlex.split(cmd)
        if not parts:
            return "Ошибка: недопустимая команда"
        
        command_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Проверка наличия команды в белом списке
        if command_name not in self.allowed_commands:
            allowed_list = ", ".join(sorted(self.allowed_commands.keys()))
            similar_commands = self._find_similar_commands(command_name)
            error_msg = f"🚫 Команда '{command_name}' не входит в список разрешённых."
            error_msg += f"\n\n✅ Разрешённые команды: {allowed_list}"
            if similar_commands:
                error_msg += f"\n💡 Возможно, вы имели в виду: {', '.join(similar_commands)}?"
            error_msg += f"\n\n📖 Введите 'help' или '?' для справки по командам"
            return error_msg
        
        # Проверка аргументов
        allowed_args = self.allowed_commands[command_name]
        
        # Улучшенная логика проверки аргументов
        if "*" not in allowed_args and args:
            validation_result = self._validate_parameters(command_name, args)
            if not validation_result[0]:  # проверка не пройдена
                return validation_result[1]
        
        # Если разрешены любые аргументы — базовая проверка безопасности
        elif "*" in allowed_args and args:
            validation_result = self._validate_wildcard_args(command_name, args)
            if not validation_result[0]:  # проверка не пройдена
                return validation_result[1]
        
        # Выполнение команды (shell=False повышает безопасность)
        try:
            # shlex.split корректно обрабатывает аргументы в кавычках
            result = subprocess.run(
                cmd,
                shell=True,  # обратная совместимость, но с более строгим белым списком
                capture_output=True,
                text=True,
                timeout=15,
                cwd=None  # ограничение выполнения безопасным каталогом
            )
            
            # Объединение стандартного вывода и ошибок
            output = result.stdout
            if result.stderr:
                output += f"\n[стандартная ошибка]\n{result.stderr}"
            
            # Возврат результата выполнения
            if result.returncode == 0:
                return output.strip() if output.strip() else "Команда выполнена успешно (без вывода)"
            else:
                return f"Ошибка выполнения команды (код возврата: {result.returncode})\n{output.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Превышено время ожидания выполнения команды (более 15 секунд)."
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
            return f"Ошибка выполнения команды: {error_output or str(e)}"
        except Exception as e:
            return f"Исключение при выполнении: {str(e)}"

    def _validate_parameters(self, command_name, args):
        """Проверяет аргументы конкретной команды
        
        Args:
            command_name: имя команды
            args: список аргументов
            
        Returns:
            tuple: (is_valid, error_message)
        """
        allowed_args = self.allowed_commands[command_name]
        
        # Проверка опций
        option_args = [arg for arg in args if arg.startswith("-")]
        for arg in option_args:
            if arg not in allowed_args and arg != "-p":  # -p особый, разрешён для mkdir
                help_text = self._get_command_help(command_name)
                return False, f"Аргумент '{arg}' не разрешён.\n{help_text}"
        
        # Проверка неопциональных аргументов (обычно пути к файлам)
        file_args = [arg for arg in args if not arg.startswith("-")]
        for arg in file_args:
            if self._is_dangerous_path(arg):
                return False, f"Опасный путь: {arg}\nДоступ разрешён только к текущему каталогу и его подкаталогам"
        
        return True, None

    def _validate_wildcard_args(self, command_name, args):
        """Проверяет аргументы с подстановочными знаками (для cat, echo и т.п.)
        
        Args:
            command_name: имя команды
            args: список аргументов
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Для файловых команд — проверка безопасности путей
        if command_name in ["cat", "head", "tail", "grep"]:
            for arg in args:
                if not arg.startswith("-") and self._is_dangerous_path(arg):
                    return False, f"Опасный путь: {arg}\nДоступ разрешён только к текущему каталогу и его подкаталогам"
        
        return True, None

    def _is_dangerous_path(self, path):
        """Проверяет, является ли путь опасным
        
        Args:
            path: проверяемый путь
            
        Returns:
            bool: опасен ли путь
        """
        # Проверка абсолютных путей
        if os.path.isabs(path):
            return True
        
        # Проверка путей с опасными символами
        dangerous_patterns = ["../", "..\\", "~/", "/etc", "/bin", "/usr", "/var", "/sys"]
        for pattern in dangerous_patterns:
            if pattern in path:
                return True
        
        return False

    def _get_command_help(self, command_name):
        """Возвращает справку по использованию команды
        
        Args:
            command_name: имя команды
            
        Returns:
            str: справочная информация
        """
        help_text = {
            "pwd": "Использование: pwd\nНазначение: показать текущий рабочий каталог",
            "ls": "Использование: ls [-la] [путь]\nНазначение: вывести содержимое каталога\nОпции: -l (подробно), -a (скрытые файлы)",
            "cat": "Использование: cat <имя_файла>\nНазначение: показать содержимое файла",
            "head": "Использование: head [-n число_строк] <файл>\nНазначение: показать начало файла",
            "tail": "Использование: tail [-n число_строк] <файл>\nНазначение: показать конец файла",
            "wc": "Использование: wc [-l|-w] <файл>\nНазначение: подсчёт строк и слов\nОпции: -l (строки), -w (слова)",
            "echo": "Использование: echo <текст>\nНазначение: вывести текст",
            "whoami": "Использование: whoami\nНазначение: показать имя текущего пользователя",
            "date": "Использование: date\nНазначение: показать текущие дату и время",
            "uname": "Использование: uname [-a]\nНазначение: показать системную информацию\nОпции: -a (вся информация)",
            "find": "Использование: find . [опции]\nНазначение: поиск файлов\nПримечание: поиск только в текущем каталоге",
            "cd": "Использование: cd <каталог>\nНазначение: перейти в указанный каталог",
            "mkdir": "Использование: mkdir [-p] <имя_каталога>\nНазначение: создать каталог\nОпции: -p (рекурсивно)",
            "touch": "Использование: touch <имя_файла>\nНазначение: создать пустой файл",
            "grep": "Использование: grep [-inr] 'шаблон' <файл>\nНазначение: поиск текста\nОпции: -i (без учёта регистра), -n (номера строк), -r (рекурсивно)",
            "which": "Использование: which <команда>\nНазначение: найти расположение команды",
            "whereis": "Использование: whereis <программа>\nНазначение: найти расположение программы",
            "du": "Использование: du [-hs] [путь]\nНазначение: показать использование диска\nОпции: -h (читаемый формат), -s (итого)",
            "df": "Использование: df [-h]\nНазначение: показать информацию о файловой системе\nОпции: -h (читаемый формат)"
        }
        return help_text.get(command_name, f"Для команды '{command_name}' справка отсутствует")

    def _find_similar_commands(self, command_name):
        """Ищет похожие имена команд
        
        Args:
            command_name: введённое имя команды
            
        Returns:
            list: список похожих команд
        """
        import difflib
        
        # Получаем все разрешённые команды
        allowed_commands = list(self.allowed_commands.keys())
        
        # Ищем похожие команды через difflib
        similar = difflib.get_close_matches(command_name, allowed_commands, n=3, cutoff=0.6)
        
        return similar
