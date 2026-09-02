# core/main_agent.py
"""Главный агент — координационный слой, распознавание намерений и маршрутизация"""

from hello_agents import SimpleAgent, HelloAgentsLLM
from core.file_manager import FileManager


class MainAgent(SimpleAgent):
    """
    Системный координатор: распознавание намерений и маршрутизация

    Обязанности:
    - Принимать ввод пользователя
    - Распознавать намерения пользователя (create/add/vibe/summary/help/exit)
    - Маршрутизировать к соответствующим под-агентам или обработчикам
    - Управлять базовыми командами (help, list, exit)
    """

    # Сопоставление ключевых слов намерений (по приоритету, более конкретные первыми)
    INTENT_KEYWORDS = {
        "create": [
            "/create",
            "создать план",
            "составить путь обучения",
            "хочу изучить",
            "хочу учиться",
            "план обучения",  # без отдельного «обучение», чтобы избежать конфликтов
        ],
        "add": ["/add", "добавить заметку", "записать знание", "добавить знание"],
        "vibe": ["/vibe", "начать обучение", "интерактивное обучение", "практика", "проверка знаний"],
        "summary": ["/summary", "прогресс обучения", "итоги", "оценка"],
        "help": ["/help", "помощь", "help"],
        "list": ["/list", "показать все", "все области", "список"],
        "exit": ["/exit", "выход", "quit", "exit"],
    }

    def __init__(self, llm: HelloAgentsLLM, file_manager: FileManager, streaming: bool = None):
        """
        Инициализация главного агента

        Args:
            llm: экземпляр HelloAgentsLLM
            file_manager: экземпляр FileManager
            streaming: включить потоковый вывод (None = автоопределение)
        """
        system_prompt = """
        Вы — главный интерфейс обучающего ассистента LearningAgent.

        Поддерживаемые функции:
        1. Создать план (/create, «хочу учиться»)
        2. Добавить заметку (/add, «добавить заметку»)
        3. Интерактивное обучение (/vibe, «начать обучение»)
        4. Итоги (/summary, «итоги»)
        5. Справка (/help, «помощь»)
        6. Показать все области (/list)
        7. Выход (/exit, «выход»)

        После распознавания намерения пользователя вызывайте соответствующую функцию.
        При неясном намерении уточните у пользователя.
        """

        self.llm = llm
        self.file_manager = file_manager

        # Поддержка потокового вывода
        from utils.streaming import should_stream
        self.streaming = should_stream(streaming)

        # Управление состоянием сессии
        self.active_session = None  # {"domain": str, "mode": str, "round": int}

        # Инициализация через родительский класс
        super().__init__("MainAgent", llm, system_prompt)

    def _identify_intent(self, user_input: str) -> str:
        """
        Распознать намерение пользователя

        Args:
            user_input: ввод пользователя

        Returns:
            тип намерения (create/add/vibe/summary/help/list/exit/unknown)
        """
        user_input_lower = user_input.lower().strip()

        # Проверить ключевые слова каждого намерения
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    return intent

        return "unknown"

    def process_command(self, user_input: str) -> str:
        """
        Обработать команду пользователя

        Args:
            user_input: ввод пользователя

        Returns:
            результат обработки
        """
        # Проверить активную сессию vibe
        if self.active_session is not None:
            # Проверить, нужно ли завершить сессию
            if self._is_exit_command(user_input):
                return self._end_vibe_session()
            # Иначе продолжить диалог
            return self._continue_vibe_session(user_input)

        # Обычная обработка команд
        intent = self._identify_intent(user_input)

        if intent == "create":
            return self._route_to_create_plan(user_input)
        elif intent == "add":
            return self._route_to_add_knowledge(user_input)
        elif intent == "vibe":
            return self._route_to_vibe_learning(user_input)
        elif intent == "summary":
            return self._route_to_summary(user_input)
        elif intent == "help":
            return self._show_help()
        elif intent == "list":
            return self._list_domains()
        elif intent == "exit":
            return "EXIT"
        elif intent == "unknown":
            return "❓ Неизвестная команда. Введите /help для справки."

    def _route_to_create_plan(self, input_data: str) -> str:
        """
        Маршрутизация к CreatePlanAgent

        Args:
            input_data: ввод пользователя

        Returns:
            результат выполнения
        """
        from agents.create_plan_agent import CreatePlanAgent

        try:
            # Убрать префикс команды, оставить только аргументы
            # Поддержка: "/create math", "создать план math", "хочу учиться math"
            clean_input = input_data

            # Убрать префикс /create
            for prefix in ["/create", "/CREATE"]:
                if clean_input.startswith(prefix):
                    clean_input = clean_input[len(prefix) :].strip()
                    break

            # Для естественного языка оставить как есть
            # Например: «хочу учиться математике», «создать план обучения»
            if not clean_input or clean_input == input_data:
                clean_input = input_data

            agent = CreatePlanAgent(self.llm, streaming=self.streaming)
            return agent.run(clean_input)
        except Exception as e:
            return f"❌ Ошибка создания плана обучения: {e}"

    def _route_to_add_knowledge(self, input_data: str) -> str:
        """
        Маршрутизация к AddKnowledgeProcessor

        Args:
            input_data: ввод пользователя

        Returns:
            результат выполнения
        """
        from processors.add_knowledge import AddKnowledgeProcessor

        try:
            # Убрать префикс команды, оставить только аргументы
            # Пример: "/add math algo", "добавить заметку", "записать знание"
            clean_input = input_data

            # Убрать префикс /add
            for prefix in ["/add", "/ADD"]:
                if clean_input.startswith(prefix):
                    clean_input = clean_input[len(prefix) :].strip()
                    break

            # При естественном языке запросить у пользователя содержание и область
            if not clean_input or clean_input == input_data or len(clean_input) < 10:
                return self._ask_for_knowledge_input()

            # Разбор ввода (формат: область содержание)
            # Например: «машинное обучение алгоритм дерева решений»
            parts = clean_input.split(maxsplit=1)
            if len(parts) == 2:
                domain, content = parts
                domain = domain.strip()
                content = content.strip()
            else:
                # Не удалось разобрать — запросить у пользователя
                return self._ask_for_knowledge_input()

            processor = AddKnowledgeProcessor(self.llm, self.file_manager)
            return processor.add(domain, content)
        except Exception as e:
            return f"❌ Ошибка добавления знания: {e}"

    def _ask_for_knowledge_input(self) -> str:
        """
        Запросить у пользователя содержание знания и область

        Returns:
            текст подсказки
        """
        return """📝 Добавление заметки

Введите в следующем формате:

> /add <область> <содержание>

Например:
> /add машинное_обучение # кратко об алгоритме дерева решений

Или введите содержание напрямую (область будет запрошена):
> /add Дерево решений — алгоритм обучения с учителем для классификации и регрессии...

💡 Подсказка: длинный текст можно подготовить в редакторе и вставить целиком.
"""

    def _route_to_vibe_learning(self, input_data: str) -> str:
        """
        Маршрутизация к VibeLearningAgent

        Args:
            input_data: ввод пользователя

        Returns:
            результат выполнения
        """
        from agents.vibe_learning_agent import VibeLearningAgent

        try:
            # Убрать префикс команды, оставить только аргументы
            # Поддержка: "/vibe Python", "/vibe Python --mode quiz"
            clean_input = input_data

            # Убрать префикс /vibe
            for prefix in ["/vibe", "/VIBE", "/Vibe"]:
                if clean_input.startswith(prefix):
                    clean_input = clean_input[len(prefix):].strip()
                    break

            # При естественном языке запросить у пользователя
            if not clean_input or len(clean_input.split()) < 1:
                return self._ask_for_vibe_input()

            # Разбор ввода
            # формат: <область> [--mode <mode>]
            parts = clean_input.split()
            domain = parts[0].strip()

            # Проверить опцию режима
            mode = "free"  # режим по умолчанию
            if "--mode" in parts:
                mode_idx = parts.index("--mode")
                if mode_idx + 1 < len(parts):
                    mode = parts[mode_idx + 1].strip().lower()
                    if mode not in ["free", "quiz"]:
                        return "❌ Неверный режим. Используйте --mode free или --mode quiz"

            # Запустить сессию обучения
            agent = VibeLearningAgent(self.llm, self.file_manager,
                                     streaming=self.streaming)
            result = agent.start_session(domain, mode=mode)

            # Установить активную сессию
            self.active_session = {
                "domain": domain,
                "mode": mode,
                "round": 1,
                "agent": agent,
                "streaming": self.streaming  # сохранить настройку streaming
            }

            return result

        except Exception as e:
            return f"❌ Ошибка запуска интерактивного обучения: {e}"

    def _route_to_summary(self, input_data: str) -> str:
        """
        Маршрутизация к SummaryAgent

        Args:
            input_data: ввод пользователя

        Returns:
            результат выполнения
        """
        from agents.summary_agent import SummaryAgent

        try:
            # Убрать префикс команды, оставить только аргументы
            # Поддержка: "/summary Python", "итоги прогресса обучения"
            clean_input = input_data

            # Убрать префикс /summary
            for prefix in ["/summary", "/SUMMARY", "/Summary"]:
                if clean_input.startswith(prefix):
                    clean_input = clean_input[len(prefix):].strip()
                    break

            # При естественном языке запросить у пользователя
            if not clean_input or len(clean_input.split()) < 1:
                return self._ask_for_summary_input()

            # Разбор ввода
            # формат: <область>
            domain = clean_input.split()[0].strip()

            # Сгенерировать итоги обучения
            agent = SummaryAgent(self.llm, self.file_manager,
                                streaming=self.streaming)
            return agent.run(domain)

        except Exception as e:
            return f"❌ Ошибка генерации итогов обучения: {e}"

    def _is_exit_command(self, user_input: str) -> bool:
        """
        Проверить, является ли команда выходом

        Args:
            user_input: ввод пользователя

        Returns:
            является ли командой выхода
        """
        exit_keywords = ["/exit", "exit", "выход", "quit", "/quit", "завершить", "готово"]
        return user_input.strip().lower() in exit_keywords

    def _end_vibe_session(self) -> str:
        """
        Завершить сессию vibe

        Returns:
            сообщение о завершении
        """
        domain = self.active_session["domain"]
        mode = self.active_session["mode"]
        rounds = self.active_session["round"]

        # Очистить состояние сессии
        self.active_session = None

        return f"""✅ Сессия завершена

📁 Область: {domain}
📝 Режим: {mode}
💬 Число раундов диалога: {rounds}

💡 Контекст сохранён. Введите /help для списка команд.
"""

    def _continue_vibe_session(self, user_input: str) -> str:
        """
        Продолжить сессию vibe

        Args:
            user_input: ответ пользователя

        Returns:
            обратная связь и следующий вопрос
        """
        try:
            agent = self.active_session["agent"]
            domain = self.active_session["domain"]
            mode = self.active_session["mode"]

            # Согласовать настройку streaming
            agent.streaming = self.active_session.get("streaming", agent.streaming)

            # Продолжить диалог (обратная связь и следующий вопрос)
            result = agent.continue_session(domain, user_input, mode)

            # Увеличить счётчик раундов
            self.active_session["round"] += 1

            return result

        except Exception as e:
            # При ошибке очистить состояние сессии
            self.active_session = None
            return f"❌ Ошибка в диалоге: {e}\n\nСессия завершена."

    def _ask_for_vibe_input(self) -> str:
        """
        Запросить параметры интерактивного обучения

        Returns:
            текст подсказки
        """
        return """📝 Интерактивное обучение

Введите в следующем формате:

> /vibe <область> [--mode <режим>]

Например:
> /vibe Python
> /vibe Python --mode quiz

Описание режимов:
- free: свободный диалог (по умолчанию)
- quiz: режим теста

💡 Сначала создайте план обучения через /create.
"""

    def _ask_for_summary_input(self) -> str:
        """
        Запросить параметры итогов обучения

        Returns:
            текст подсказки
        """
        return """📝 Итоги прогресса обучения

Введите в следующем формате:

> /summary <область>

Например:
> /summary Python
> /summary машинное_обучение

💡 Сначала создайте план обучения через /create.
"""

    def _show_help(self) -> str:
        """Показать справку"""
        return """
# 🤖 Справка LearningAgent

## Список команд

### Создание плана обучения
- `/create <область>` — создать план обучения
  Пример: `/create математика`
  Пример: `/create https://github.com/user/project`
  Пример: `/create ~/paper.pdf`

- Естественный язык: «хочу учиться математике»

### Добавление заметок ✨ новая функция
- `/add <область> <содержание>` — добавить заметку
  Пример: `/add ML # кратко о дереве решений`
  Пример: `/add Python пример list comprehension...`

- Из файла: `/add ~/notes.md`

- Естественный язык: «добавить заметку» «записать знание»

### Интерактивное обучение ✨ новая функция
- `/vibe <область>` — начать интерактивное обучение
  Пример: `/vibe Python`
  Пример: `/vibe Python --mode quiz`

- Описание режимов:
  - `free`: свободный диалог (по умолчанию)
  - `quiz`: режим теста

- Выход из сессии: «выход», «exit» или «/exit» в любой момент

- Естественный язык: «начать обучение» «потренироваться»

### Итоги обучения ✨ новая функция
- `/summary <область>` — посмотреть итоги
  Пример: `/summary Python`
  Пример: `/summary машинное_обучение`

- Естественный язык: «итоги прогресса» «оценить мой уровень»

### Прочие команды
- `/list` — показать все области обучения
- `/help` — показать справку
- `/exit` или `exit` — выйти из программы

## Подсказки
- Поддерживаются префиксы команд и естественный язык (например «хочу учиться»)
- При добавлении знаний содержание автоматически анализируется и тегируется
- В любой момент введите `/help` для справки
"""

    def _list_domains(self) -> str:
        """Показать все области обучения"""
        domains = self.file_manager.list_domains()

        if not domains:
            return "📭 Области обучения ещё не созданы.\nИспользуйте `/create` для первого плана."

        domain_list = "\n".join([f"- {domain}" for domain in domains])
        return f"# 📚 Области обучения\n\n{domain_list}\n\nВсего {len(domains)} областей"

    def list_domains(self) -> list:
        """
        Получить список всех областей

        Returns:
            список названий областей
        """
        return self.file_manager.list_domains()
