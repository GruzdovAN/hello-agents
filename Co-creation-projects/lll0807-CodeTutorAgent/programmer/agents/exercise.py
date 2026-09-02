from hello_agents import SimpleAgent, HelloAgentsLLM
from programmer.services.problem_repository import ProblemRepository
from hello_agents.tools import RAGTool
import re


class ExerciseAgent(SimpleAgent):
    """
    Агент выбора задач из локального банка (RAG + решение LLM)
    """

    def __init__(self, llm: HelloAgentsLLM):
        system_prompt = """
Ты помощник выбора задач по программированию.

Твоя задача:
- Понять требования пользователя к сложности, теме и цели обучения
- Вывести только сложность: Easy или Medium

⚠️ Важно:
- Не генерируй новые задачи
- Выводи только Easy или Medium
"""
        super().__init__(
            name="Exercise",
            llm=llm,
            system_prompt=system_prompt
        )

        root_dir = r"E:\PycharmProject_lmx\HelloAgents-main\output"
        self.repo = ProblemRepository(root_dir)

        # ===== Инициализация RAG =====
        self.rag = RAGTool(
            collection_name="rag_knowledge_base",
            rag_namespace="problems"
        )
        # ===== Нужна ли инициализация банка =====
        need_init = False

        try:
            # Пробный поиск — проверка, пуста ли база
            test = self.rag.search(query="Easy", limit=1)
            if not test:
                need_init = True
        except Exception:
            # Векторная база не существует / первый запуск
            need_init = True

        if need_init:
            # Первый запуск — добавление задач в RAG
            for problem in self.repo.problems:
                self.rag.add_text(
                    text=f"""
                Title: {problem['title']}
                Difficulty: {problem['difficulty']}
                Tags: {", ".join(problem['tags'])}
                Description: {problem['description'][:200]}
                """.strip(),
                    document_id=problem["title"]
                )
        print("✅ Векторный репозиторий задач построен")

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:

        result = super().run(input_text)
        # ========= Семантический поиск RAG =========
        rag_results = self.rag.search(
            query=result,
            limit=3,
            min_score=0.3
        )
        titles = re.findall(r"Title:\s*(.+)", rag_results)

        user_problems = []
        # ========= Точная фильтрация локального банка =========
        for title in titles:
            problem = self.get_problem_by_title(title)
            if problem:
                user_problems.append(problem)

        if not user_problems:
            return "❌ Подходящие задачи не найдены"

        # ========= Стандартизированный результат =========
        return "\n\n".join(
            self._format_problem(problem)
            for problem in user_problems
        )

    def get_problem_by_title(self, title: str):
        for problem in self.repo.problems:
            if problem.get("title") == title:
                return problem
        return None

    def _format_problem(self, problem: dict) -> str:
        examples_md = ""

        for i, ex in enumerate(problem["examples"], start=1):
            examples_md += f"""
    **Example {i}**

    Input: {ex["input"]}  
    Output: {ex["output"]}  
    """
            if ex["explanation"]:
                examples_md += f"Explanation: {ex['explanation']}\n"

        return f"""
    ### Рекомендуемая задача: {problem['title']}

    **Difficulty:** {problem['difficulty']}  
    **Tags:** {", ".join(problem['tags'])}

    ---

    ## 📘 Описание задачи

    {problem['description']}

    ---

    ## 🧪 Примеры
    {examples_md}

    ---

    ## 📌 Ограничения

    {problem['constraints']}

    ---

    💡 *Попробуйте решить самостоятельно, не смотрите решение. После завершения отправьте код для ревью.*
    """
