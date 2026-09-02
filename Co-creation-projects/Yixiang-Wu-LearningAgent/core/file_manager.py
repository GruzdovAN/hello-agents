# core/file_manager.py
"""Файловый менеджер - унифицированное управление всеми файловыми операциями в ~/.learningAgent/"""

from pathlib import Path
from datetime import datetime
from typing import List
from utils.exceptions import FileReadError, FileWriteError


class FileManager:
    """
Унифицированное управление всеми файловыми операциями в ~/.learningAgent/

    Attributes:
BASE_DIR: путь к базовому каталогу.
    """

    BASE_DIR = Path.home() / ".learningAgent"

    def __init__(self):
"""Инициализируйте файловый менеджер и убедитесь, что базовый каталог существует"""
        self.ensure_structure()

    def ensure_structure(self) -> None:
"""Убедитесь, что базовая структура каталогов существует"""
        self.BASE_DIR.mkdir(exist_ok=True)

    def create_domain(self, domain: str) -> None:
        """
Создать новый каталог учебных территорий

        Args:
домен: доменное имя
        """
        domain_path = self.BASE_DIR / domain
        domain_path.mkdir(exist_ok=True)
        (domain_path / "knowledge").mkdir(exist_ok=True)
        (domain_path / "sessions").mkdir(exist_ok=True)

# Создаем пустой файл сводки
        (domain_path / "knowledge" / "knowledge_summary.md").write_text(
            "# 知识总结\n\n> 暂无知识笔记\n", encoding="utf-8"
        )
        (domain_path / "sessions" / "session_summary.md").write_text(
            "# 学习历程\n\n> 暂无学习记录\n", encoding="utf-8"
        )

    def save_plan(self, domain: str, plan_content: str) -> None:
        """
Сохранить план обучения

        Args:
домен: доменное имя
plan_content: содержимое плана (формат уценки)
        """
        plan_path = self.BASE_DIR / domain / "plan.md"
        try:
            plan_path.write_text(plan_content, encoding="utf-8")
        except Exception as e:
            raise FileWriteError(f"无法保存学习计划：{e}")

    def save_knowledge(self, domain: str, filename: str, content: str) -> None:
        """
Сохраняйте заметки по знаниям

        Args:
домен: доменное имя
имя файла: имя файла
содержимое: содержимое файла
        """
        knowledge_path = self.BASE_DIR / domain / "knowledge" / filename
        try:
            knowledge_path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise FileWriteError(f"无法保存知识笔记：{e}")

    def save_session(self, domain: str, session_content: str) -> Path:
        """
Сохраняйте записи отдельных сеансов обучения

        Args:
домен: доменное имя
session_content: содержимое сеанса

        Returns:
Сохраненный путь к файлу
        """
        date = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H-%M")
        session_path = self.BASE_DIR / domain / "sessions" / f"session_{date}_{time}.md"

        try:
            session_path.write_text(session_content, encoding="utf-8")
        except Exception as e:
поднять FileWriteError(f «Невозможно сохранить запись сеанса: {e}»)

        return session_path

    def read_plan(self, domain: str) -> str:
        """
Чтение учебного плана

        Args:
домен: доменное имя

        Returns:
Планирование контента

        Raises:
FileNotFoundError: если план не существует
        """
        plan_path = self.BASE_DIR / domain / "plan.md"
        if not plan_path.exists():
            raise FileNotFoundError(f"学习计划不存在：{domain}")

        try:
            return plan_path.read_text(encoding="utf-8")
        except Exception as e:
            raise FileReadError(f"无法读取学习计划：{e}")

    def domain_exists(self, domain: str) -> bool:
        """
Проверьте, существует ли область

        Args:
домен: доменное имя

        Returns:
существует
        """
        return (self.BASE_DIR / domain).exists()

    def list_domains(self) -> List[str]:
        """
Перечислите все направления обучения

        Returns:
Список названий сфер
        """
        if not self.BASE_DIR.exists():
            return []

        return [d.name for d in self.BASE_DIR.iterdir() if d.is_dir()]
