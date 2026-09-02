# specialist/repo_analyzer.py
"""GitHub 仓库分析专家"""

import re
from typing import Dict, List, Optional
import requests
from hello_agents import HelloAgentsLLM


class RepoAnalyzerAgent:
    """
Эксперт по анализу склада GitHub

Функция:
- Извлеките информацию о репозитории из URL-адреса GitHub.
- Получить основную информацию о проекте (описание, язык, звезды и т. д.)
- Получить и проанализировать содержимое README.
- Определить технологический стек
- Сделайте вывод о требованиях к предварительным знаниям
    """

    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self, llm: HelloAgentsLLM, github_token: Optional[str] = None):
        """
Инициализация агента RepoAnalyzerAgent

        Args:
llm: экземпляр HelloAgentsLLM
            github_token: GitHub API Token（可选，用于提高速率限制）
        """
        self.llm = llm
        self.github_token = github_token
        self.headers = {}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

    def _extract_repo_info(self, url: str) -> tuple[str, str]:
        """
Извлечь владельца и имя репо из URL-адреса GitHub.

        Args:
            url: GitHub URL（如 https://github.com/vuejs/core）

        Returns:
(владелец, репо) кортеж
        """
# Удаляем суффикс .git
        url = url.rstrip(".git")

# Извлекаем владельца и репозиторий
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            owner = parts[-2]
            repo = parts[-1]
            return owner, repo

        raise ValueError(f"无法解析 GitHub URL: {url}")

    def _fetch_repo_info(self, owner: str, repo: str) -> Dict:
        """
Получите основную информацию о складе

        Args:
владелец: владелец склада
репо: название склада

        Returns:
Словарь складской информации
        """
        url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    def _fetch_readme(self, owner: str, repo: str) -> Optional[str]:
        """
Получить содержимое README

        Args:
владелец: владелец склада
репо: название склада

        Returns:
Текстовое содержимое README, возвращает None, если оно не существует.
        """
        try:
            url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
# Содержимое README имеет кодировку Base64.
                import base64

                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
        except Exception:
            pass
        return None

    def _extract_tech_stack_from_text(self, text: str) -> List[str]:
        """
Извлечение ключевых слов стека технологий из текста

        Args:
текст: текстовое содержимое

        Returns:
Список технологических стеков
        """
# Общие технические ключевые слова
        tech_keywords = [
            "React",
            "Vue",
            "Angular",
            "Svelte",
            "TypeScript",
            "JavaScript",
            "Python",
            "Java",
            "Go",
            "Rust",
            "Node.js",
            "Django",
            "Flask",
            "FastAPI",
            "Express",
            "TensorFlow",
            "PyTorch",
            "Keras",
            "Docker",
            "Kubernetes",
            "MongoDB",
            "PostgreSQL",
            "MySQL",
            "Redis",
            "TailwindCSS",
            "Bootstrap",
            "CSS",
            "HTML",
        ]

        found_techs = []
        text_lower = text.lower()

        for tech in tech_keywords:
            if tech.lower() in text_lower:
                found_techs.append(tech)

        return found_techs

    def _analyze_with_llm(
        self, repo_info: Dict, readme: Optional[str]
    ) -> Dict[str, any]:
        """
Используйте LLM для углубленного анализа склада

        Args:
repo_info: основная информация о складе
readme: содержимое README (необязательно)

        Returns:
Словарь результатов анализа
        """
# Подсказки для анализа сборки
        repo_name = repo_info.get("name", "unknown")
        description = repo_info.get("description", "")
        language = repo_info.get("language", "")
        topics = repo_info.get("topics", [])

        user_prompt = f"""请分析以下 GitHub 仓库并提取学习相关信息：

[Название склада]
{repo_name}

【описывать】
{description}

【Основной язык】
{language}

[тег темы]
{', '.join(topics), если темы else '无'}

"""

        if readme:
            user_prompt += f"""
[Содержимое README]
{readme[:2000]} #Ограничить длину
"""

        user_prompt += """
Пожалуйста, предоставьте следующую информацию (формат JSON):
{
  "domain": "学习领域（如 web-development, data-science 等）",
"tech_stack": ["Технология1", "Технология2", "..."],
"предпосылки": ["Необходимые знания 1", "Необходимые знания 2", "..."],
"learning_difficulty": "Элементарный/Средний/Продвинутый",
"estimated_weeks": количество недель, необходимое для обучения (целое число).
}
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个技术教育专家，擅长分析开源项目并提取学习相关信息。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.llm.invoke(messages)
# Упрощенная реализация: возврат основной информации (JSON, возвращаемый LLM, фактически должен быть проанализирован)
            return {
                "domain": repo_name.lower().replace("-", " "),
                "tech_stack": self._extract_tech_stack_from_text(
                    description + " " + language
                ),
                "prerequisites": [],
"learning_difficulty": "中级",
                "estimated_weeks": 4,
            }
        except Exception:
# Понижение версии: используйте анализ на основе правил.
            return {
                "domain": repo_name.lower().replace("-", " "),
                "tech_stack": [language] if language else [],
                "prerequisites": [],
"learning_difficulty": "中级",
                "estimated_weeks": 4,
            }

    def analyze(self, github_url: str) -> Dict[str, any]:
        """
Анализ репозиториев GitHub

        Args:
github_url: URL-адрес репозитория GitHub.

        Returns:
Словарь результатов анализа, включающий:
- домен: область исследования
- tech_stack: список технологических стеков
- пререквизиты: список необходимых знаний
- описание: описание проекта
- язык: основной язык
- звезды: количество звезд
        """
# Извлечь информацию о складе
        owner, repo = self._extract_repo_info(github_url)

# Получите основную информацию
        repo_info = self._fetch_repo_info(owner, repo)

# Получите README
        readme = self._fetch_readme(owner, repo)

# Извлекаем стек технологий (на основе правил)
        tech_stack = []
        if repo_info.get("language"):
            tech_stack.append(repo_info["language"])

        if readme:
            tech_stack.extend(self._extract_tech_stack_from_text(readme))

# Удаляем дубликаты
        tech_stack = list(set(tech_stack))

# Глубокий анализ с использованием LLM (если доступно)
        llm_analysis = self._analyze_with_llm(repo_info, readme)

# Объединить результаты
        result = {
            "domain": llm_analysis.get("domain", repo.lower().replace("-", " ")),
            "tech_stack": tech_stack,
            "prerequisites": llm_analysis.get("prerequisites", []),
            "description": repo_info.get("description", ""),
            "language": repo_info.get("language", ""),
            "stars": repo_info.get("stargazers_count", 0),
"learning_difficulty": llm_anaанализ.get("learning_difficulty", "中级"),
            "estimated_weeks": llm_analysis.get("estimated_weeks", 4),
        }

        return result
