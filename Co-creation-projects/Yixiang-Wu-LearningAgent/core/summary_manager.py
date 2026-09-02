# core/summary_manager.py
"""Диспетчер обновлений дайджеста — смешанная стратегия: полная перезапись <5 файлов, ≥5 дополнительных обновлений"""

from pathlib import Path
from typing import List
from hello_agents import HelloAgentsLLM
from config import Config


class SummaryManager:
    """
Управляйте обновлениями сводок знаний и сводок бесед.

Используйте смешанную стратегию:
- Количество файлов < 5: полностью переписать сводку.
- Количество файлов ≥ 5: сводка дополнительных обновлений.

    Attributes:
fm: экземпляр FileManager
llm: экземпляр HelloAgentsLLM
    """

    def __init__(self, file_manager):
        """
Инициализировать менеджер сводок

        Args:
file_manager: экземпляр FileManager
        """
        self.fm = file_manager
        self.llm = HelloAgentsLLM()

    def update_knowledge_summary(self, domain: str, new_file: str) -> None:
        """
Обновить Knowledge_summary.md

        Args:
домен: доменное имя
new_file: новое добавленное имя файла.
        """
        domain_path = self.fm.BASE_DIR / domain
        knowledge_dir = domain_path / "knowledge"
        summary_path = knowledge_dir / "knowledge_summary.md"

# Подсчитаем количество файлов (исключая summary.md)
        existing_files: List[Path] = list(knowledge_dir.glob("*.md"))
        file_count = len(
            [f for f in existing_files if f.name != "knowledge_summary.md"]
        )

        if file_count < Config.SUMMARY_FULL_REWRITE_THRESHOLD:
            self._full_rewrite_knowledge_summary(domain, knowledge_dir, summary_path)
        else:
            self._incremental_update_knowledge_summary(domain, new_file, summary_path)

    def _full_rewrite_knowledge_summary(
        self, domain: str, knowledge_dir: Path, summary_path: Path
    ) -> None:
        """
Полностью переписать сводку знаний

        Args:
домен: доменное имя
Knowledge_dir: каталог знаний
summary_path: путь к файлу сводки
        """
# Прочитать все файлы знаний
        all_files: List[Path] = [
            f for f in knowledge_dir.glob("*.md") if f.name != "knowledge_summary.md"
        ]
        all_content = []
        for file in all_files:
            content = file.read_text(encoding="utf-8")
            all_content.append(f"## {file.stem}\n{content}\n")

        # 让 LLM 生成压缩摘要
        user_prompt = f"""以下是 {domain} 领域的所有知识笔记，请生成一个结构化的总结摘要：

{''.join(all_content)}

Требовать:
1. Организовано по темам
2. Извлеките основные понятия и ключевые моменты знаний.
3. Сохраняйте структуру (формат уценки)
4. Контролируйте длину до 20 % от исходного контента.
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个知识总结助手，擅长提取核心概念并生成结构化摘要。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            summary = self.llm.invoke(messages)
            summary_path.write_text(summary, encoding="utf-8")
        except Exception:
# Если вызов LLM не удался, используйте простое слияние
Fallback_summary = f"# {domain} Сводка знаний\n\n" + "\n".join(all_content)
            summary_path.write_text(fallback_summary, encoding="utf-8")

    def _incremental_update_knowledge_summary(
        self, domain: str, new_file: str, summary_path: Path
    ) -> None:
        """
Постепенно обновляйте сводки знаний

        Args:
домен: доменное имя
новый_файл: новое имя файла
summary_path: путь к файлу сводки
        """
# Прочитать текущую сводку и новые файлы
        current_summary = summary_path.read_text(encoding="utf-8")
        new_content = (self.fm.BASE_DIR / domain / "knowledge" / new_file).read_text(
            encoding="utf-8"
        )

# Позвольте LLM объединиться
user_prompt = f"""Текущая сводка:
{current_summary}

Новый контент:
{new_content}

Пожалуйста, интегрируйте новый контент в аннотацию и сохраняйте ее структурированность и краткость.
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个知识总结助手，擅长整合新内容到现有摘要中。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            updated_summary = self.llm.invoke(messages)
            summary_path.write_text(updated_summary, encoding="utf-8")
        except Exception:
# Если вызов LLM не удался, используйте простое добавление
            updated_summary = (
                current_summary + f"\n\n## {Path(new_file).stem}\n{new_content}"
            )
            summary_path.write_text(updated_summary, encoding="utf-8")

    def update_session_summary(self, domain: str, new_session_content: str) -> None:
        """
Обновить session_summary.md

        Args:
домен: доменное имя
new_session_content: новый контент сеанса
        """
        domain_path = self.fm.BASE_DIR / domain
        sessions_dir = domain_path / "sessions"
        summary_path = sessions_dir / "session_summary.md"

# Подсчитаем количество файлов
        existing_files: List[Path] = list(sessions_dir.glob("session_*.md"))
        file_count = len(
            [f for f in existing_files if not f.name.startswith("session_summary")]
        )

        if file_count < Config.SUMMARY_FULL_REWRITE_THRESHOLD:
            self._full_rewrite_session_summary(domain, sessions_dir, summary_path)
        else:
            self._incremental_update_session_summary(new_session_content, summary_path)

    def _full_rewrite_session_summary(
        self, domain: str, sessions_dir: Path, summary_path: Path
    ) -> None:
        """
Полностью переписано резюме сеанса.
        """
        all_sessions: List[Path] = [
            f
            for f in sessions_dir.glob("session_*.md")
            if not f.name.startswith("session_summary")
        ]
        all_content = []
        for file in all_sessions:
            content = file.read_text(encoding="utf-8")
            all_content.append(f"## {file.stem}\n{content}\n")

        user_prompt = f"""以下是 {domain} 领域的所有学习会话记录，请生成一个压缩的总结：

{''.join(all_content)}

Требовать:
1. Извлеките ключевые моменты обучения
2. Запишите прогресс
3. Определите контент, требующий проверки.
4. Контролируйте длину до 30 % от исходного контента.
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个学习历程总结助手，擅长提取关键学习点和进步轨迹。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            summary = self.llm.invoke(messages)
            summary_path.write_text(summary, encoding="utf-8")
        except Exception:
Fallback_summary = f"# {domain} Процесс обучения\n\n" + "\n".join(all_content)
            summary_path.write_text(fallback_summary, encoding="utf-8")

    def _incremental_update_session_summary(
        self, new_session_content: str, summary_path: Path
    ) -> None:
        """
Сводка сеанса добавочного обновления
        """
        current_summary = summary_path.read_text(encoding="utf-8")

user_prompt = f"""Текущая сводка:
{current_summary}

Новая запись сессии:
{new_session_content}

Пожалуйста, включите новые разговоры в сводку.
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个学习历程总结助手，擅长整合新的学习会话到总结中。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            updated_summary = self.llm.invoke(messages)
            summary_path.write_text(updated_summary, encoding="utf-8")
        except Exception:
            updated_summary = current_summary + f"\n\n{new_session_content}"
            summary_path.write_text(updated_summary, encoding="utf-8")
