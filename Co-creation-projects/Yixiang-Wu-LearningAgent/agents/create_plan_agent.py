# agents/create_plan_agent.py
"""Агент генерации плана обучения"""

import re
from hello_agents import ReActAgent, HelloAgentsLLM
from core.file_manager import FileManager


class CreatePlanAgent(ReActAgent):
    """
    Эксперт по генерации планов обучения
    Три типа ввода: описание области, URL GitHub, PDF-статья
    """

    def __init__(self, llm: HelloAgentsLLM, streaming: bool = None):
        """
        Инициализация CreatePlanAgent

        Args:
            llm: экземпляр HelloAgentsLLM
            streaming: потоковый вывод (None = автоопределение)
        """
        self.max_steps = 5
        self.file_manager = FileManager()

        # Потоковый вывод
        from utils.streaming import should_stream
        self.streaming = should_stream(streaming)

        # Системный промпт
        system_prompt = """
        Вы — эксперт по планированию обучения. Рабочий процесс:

        1. Определить тип ввода:
           - описание области (например: «хочу учиться математике»)
           - URL GitHub (например: "https://github.com/user/project")
           - путь к PDF (например: "/path/to/paper.pdf")

        2. Для URL/файла — вызвать соответствующий инструмент для глубокого анализа

        3. Спросить у пользователя цель обучения:
           - естественным языком (например: «применять на работе», «уровень магистратуры»)

        4. По результатам анализа и цели найти лучший путь обучения в области

        5. Сформировать структурированный план (Markdown):
           - обзор области
           - требования к предварительным знаниям
           - путь обучения (по этапам)
           - рекомендуемые ресурсы
           - вехи и контрольные точки

        Формат ReAct:
        Thought: ваш ход мыслей
        Action: tool_name[input]
        Observation: результат инструмента
        ...
        Finish: [итоговый план обучения]
        """

        # Инициализация через родительский класс
        super().__init__("CreatePlanAgent", llm, system_prompt)

    def _identify_input_type(self, input_data: str) -> str:
        """
        Определить тип ввода

        Args:
            input_data: ввод пользователя

        Returns:
            тип ввода (github_url/pdf_paper/domain_description)
        """
        # Проверка URL GitHub
        if input_data.startswith("https://github.com/"):
            return "github_url"

        # Проверка пути к PDF
        if (
            input_data.endswith(".pdf")
            or input_data.startswith("~/")
            or input_data.startswith("/")
        ):
            return "pdf_paper"

        # По умолчанию — описание области
        return "domain_description"

    def _analyze_github_repo(self, url: str) -> dict:
        """
        Анализ репозитория GitHub

        Args:
            url: GitHub URL

        Returns:
            словарь результатов анализа
        """
        from specialist.repo_analyzer import RepoAnalyzerAgent
        import os

        # GitHub Token (если настроен)
        github_token = os.getenv("GITHUB_TOKEN")

        # Создать RepoAnalyzerAgent
        repo_analyzer = RepoAnalyzerAgent(self.llm, github_token)

        # Анализ репозитория
        try:
            analysis = repo_analyzer.analyze(url)
            return {
                "domain": analysis.get("domain", ""),
                "tech_stack": analysis.get("tech_stack", []),
                "prerequisites": analysis.get("prerequisites", []),
                "description": analysis.get("description", ""),
                "stars": analysis.get("stars", 0),
            }
        except Exception as e:
            # Fallback: упрощённая реализация
            repo_name = url.rstrip(".git").split("/")[-1]
            return {
                "domain": repo_name.replace("-", " ").replace("_", " "),
                "tech_stack": [],
                "prerequisites": [],
                "description": f"Ошибка анализа репозитория GitHub: {e}",
                "stars": 0,
            }

    def _analyze_pdf_paper(self, file_path: str) -> dict:
        """
        Анализ PDF-статьи

        Args:
            file_path: путь к PDF

        Returns:
            словарь результатов анализа
        """
        from specialist.paper_analyzer import PaperAnalyzerAgent

        # Создать PaperAnalyzerAgent
        paper_analyzer = PaperAnalyzerAgent(self.llm)

        # Анализ статьи
        try:
            analysis = paper_analyzer.analyze(file_path)
            return {
                "domain": analysis.get("domain", ""),
                "title": analysis.get("title", ""),
                "prerequisites": analysis.get("prerequisites", []),
                "core_concepts": analysis.get("core_concepts", []),
            }
        except Exception as e:
            # Fallback: упрощённая реализация
            import os

            filename = os.path.basename(file_path).replace(".pdf", "").replace("-", " ")
            return {
                "domain": filename,
                "title": filename,
                "prerequisites": [],
                "core_concepts": [],
                "error": f"Ошибка анализа PDF: {e}",
            }

    def _ask_learning_goal(self, analysis: dict) -> str:
        """
        Спросить цель обучения

        Args:
            analysis: результаты анализа

        Returns:
            описание цели обучения
        """
        print(f"\n📚 Результаты анализа: {analysis.get('domain', 'неизвестная область')}")
        if analysis.get("tech_stack"):
            print(f"Стек технологий: {', '.join(analysis['tech_stack'])}")
        if analysis.get("prerequisites"):
            print(f"Предварительные знания: {', '.join(analysis['prerequisites'])}")
        if analysis.get("title"):
            print(f"Название статьи: {analysis['title']}")
        if analysis.get("core_concepts"):
            print(
                f"Ключевые концепции: {', '.join(analysis['core_concepts'][:5])}"
            )  # максимум 5
        if analysis.get("description"):
            print(f"Описание: {analysis['description']}")
        if analysis.get("stars", 0) > 0:
            print(f"⭐ Stars: {analysis['stars']}")

        return input("\n🎯 Какого уровня обучения вы хотите достичь? (опишите естественным языком)\n> ")

    def _search_learning_resources(self, query: str) -> str:
        """
        Поиск учебных ресурсов

        Args:
            query: поисковый запрос

        Returns:
            результаты поиска
        """
        # Упрощённо: общие рекомендации
        return f"Ресурсы для «{query}»: онлайн-курсы, книги, документация, практические проекты"

    def _generate_plan(self, analysis: dict, goal: str, resources: str) -> str:
        """
        Сгенерировать план обучения

        Args:
            analysis: результаты анализа
            goal: цель обучения
            resources: учебные ресурсы

        Returns:
            содержание плана обучения
        """
        user_prompt = f"""Сформируйте план обучения (Markdown) для сценария:

【Область/тема】
{analysis.get('domain', 'неизвестно')}

【Стек технологий】
{', '.join(analysis.get('tech_stack', ['нет']))}

【Требования к предварительным знаниям】
{', '.join(analysis.get('prerequisites', ['нет']))}

【Цель обучения】
{goal}

【Справочные ресурсы】
{resources}

Сформируйте структурированный план:
1. Обзор области (~100 слов)
2. Чек-лист предварительных знаний
3. Поэтапный путь (3-5 этапов)
4. Конкретное содержание каждого этапа
5. Рекомендуемые ресурсы (книги, курсы, документация)
6. Вехи и критерии самооценки
"""

        messages = [
            {
                "role": "system",
                "content": "Вы — профессиональный ассистент по планированию обучения, создаёте структурированные планы.",
            },
            {"role": "user", "content": user_prompt},
        ]

        if self.streaming:
            from utils.streaming import stream_response
            return stream_response(self.llm, messages)
        else:
            return self.llm.invoke(messages)

    def run(self, input_data: str) -> str:
        """
        Выполнить создание плана обучения

        Args:
            input_data: ввод (область/URL GitHub/путь PDF)

        Returns:
            результат выполнения
        """
        # Шаг 1: определить тип ввода
        input_type = self._identify_input_type(input_data)

        # Шаг 2: обработка по типу
        if input_type == "github_url":
            analysis = self._analyze_github_repo(input_data)
        elif input_type == "pdf_paper":
            analysis = self._analyze_pdf_paper(input_data)
        else:  # domain_description
            analysis = {"domain": input_data, "tech_stack": [], "prerequisites": []}

        # Шаг 3: уточнить цель обучения
        learning_goal = self._ask_learning_goal(analysis)

        # Шаг 4: поиск пути обучения
        search_query = f"{analysis['domain']} путь обучения {learning_goal}"
        learning_resources = self._search_learning_resources(search_query)

        # Шаг 5: генерация плана
        plan = self._generate_plan(analysis, learning_goal, learning_resources)

        # Шаг 6: сохранение плана
        domain = analysis["domain"]
        self.file_manager.create_domain(domain)
        self.file_manager.save_plan(domain, plan)

        return f"✅ План обучения создан: {domain}\n\n{plan}"
