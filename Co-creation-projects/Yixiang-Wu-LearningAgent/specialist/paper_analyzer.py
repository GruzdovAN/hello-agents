# specialist/paper_analyzer.py
"""Эксперт по анализу PDF-документов"""

import os
from pathlib import Path
from typing import Dict, List
import PyPDF2
from hello_agents import HelloAgentsLLM


class PaperAnalyzerAgent:
    """
Эксперт по анализу PDF-документов

Функция:
- Читать PDF-документы
- Извлечение заголовков и аннотаций
- Определить основные понятия.
- Сделать вывод о предварительном знании
- Определить области исследований.
    """

    def __init__(self, llm: HelloAgentsLLM):
        """
Инициализация агента PaperAnalyzerAgent

        Args:
llm: экземпляр HelloAgentsLLM
        """
        self.llm = llm

    def _extract_title_from_path(self, file_path: str) -> str:
        """
Извлечь название статьи из пути к файлу

        Args:
file_path: путь к PDF-файлу

        Returns:
Название статьи
        """
# Процесс ~ путь
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)

# Получаем имя файла (удаляем расширение)
        filename = Path(file_path).stem

# Заменяем дефисы и подчеркивания пробелами
        title = filename.replace("-", " ").replace("_", " ")

        return title

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
Извлечь текст из PDF

        Args:
file_path: путь к PDF-файлу

        Returns:
Извлеченный текстовый контент
        """
# Процесс ~ путь
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)

        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""

# Извлеките содержимое первых трех страниц (обычно включая аннотацию и введение)
                max_pages = min(3, len(reader.pages))
                for i in range(max_pages):
                    page = reader.pages[i]
                    text += page.extract_text() + "\n"

                return text
        except Exception as e:
поднять IOError(f «Невозможно прочитать PDF-файл: {e}»)

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """
Извлечение ключевых слов из текста

        Args:
текст: бумажный текст

        Returns:
список ключевых слов
        """
# Общие ключевые слова в академических областях
        academic_keywords = [
# Глубокое обучение/Машинное обучение
            "Neural Network",
            "Deep Learning",
            "Transformer",
            "Attention",
            "CNN",
            "RNN",
            "LSTM",
            "Backpropagation",
            "Gradient Descent",
            "Optimization",
            # 自然语言处理
            "NLP",
            "Language Model",
            "Tokenization",
            "Embedding",
            "BERT",
            "GPT",
#компьютерное зрение
            "Computer Vision",
            "Image Processing",
            "Convolution",
            "Feature Extraction",
# другой
            "Algorithm",
            "Data Structure",
            "Complexity",
            "Statistics",
            "Probability",
        ]

        found_keywords = []
        text_lower = text.lower()

        for keyword in academic_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _identify_prerequisites(self, keywords: List[str]) -> List[str]:
        """
        根据关键词推断前置知识

        Args:
ключевые слова: список ключевых слов

        Returns:
Список необходимых знаний
        """
# Картирование предварительных знаний
        prereq_map = {
            "Deep Learning": ["Machine Learning", "Python", "Linear Algebra"],
            "Transformer": ["Attention Mechanism", "Sequence Models"],
            "Neural Network": ["Calculus", "Linear Algebra", "Probability"],
            "CNN": ["Image Processing", "Linear Algebra"],
            "RNN": ["Sequence Models", "Calculus"],
            "NLP": ["Machine Learning", "Statistics", "Python"],
            "Computer Vision": ["Linear Algebra", "Probability", "Python"],
        }

        prerequisites = []
        for keyword in keywords:
            if keyword in prereq_map:
                prerequisites.extend(prereq_map[keyword])

# Удаляем дубликаты
        return list(set(prerequisites))

    def _analyze_with_llm(self, title: str, text: str) -> Dict[str, any]:
        """
        使用 LLM 深度分析论文

        Args:
название: название статьи
текст: бумажный текст

        Returns:
Словарь результатов анализа
        """
user_prompt = f"""Проанализируйте следующие научные статьи и извлеките информацию, связанную с обучением:

【Название статьи】
{title}

[Содержание статьи (первые 1000 слов)]
{text[:1000]}
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个学术教育专家，擅长分析学术论文并提取学习相关信息。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.llm.invoke(messages)
# Упрощенная реализация: возврат результатов анализа на основе правил
            keywords = self._extract_keywords_from_text(text)
            prerequisites = self._identify_prerequisites(keywords)

            return {
                "domain": self._infer_domain_from_keywords(keywords),
                "core_concepts": keywords[:5],  # 前5个关键词
                "prerequisites": prerequisites,
                "title": title,
"learning_difficulty": "高级",
                "estimated_weeks": 8,
            }
        except Exception:
# Понижение версии: используйте анализ на основе правил.
            keywords = self._extract_keywords_from_text(text)
            prerequisites = self._identify_prerequisites(keywords)

            return {
                "domain": self._infer_domain_from_keywords(keywords),
                "core_concepts": keywords[:5],
                "prerequisites": prerequisites,
                "title": title,
"learning_difficulty": "高级",
                "estimated_weeks": 8,
            }

    def _infer_domain_from_keywords(self, keywords: List[str]) -> str:
        """
Определите области исследований на основе ключевых слов

        Args:
ключевые слова: список ключевых слов

        Returns:
область исследования
        """
        if not keywords:
            return "general"

        keyword_lower = " ".join(keywords).lower()

# Сопоставление доменов
        if any(
            kw in keyword_lower
            for kw in ["transformer", "attention", "nlp", "language", "bert", "gpt"]
        ):
            return "natural-language-processing"
        elif any(
            kw in keyword_lower
            for kw in ["cnn", "image", "vision", "computer", "processing"]
        ):
            return "computer-vision"
        elif any(
            kw in keyword_lower
            for kw in ["neural", "deep", "learning", "network", "backpropagation"]
        ):
            return "deep-learning"
        elif any(
            kw in keyword_lower for kw in ["machine", "learning", "algorithm", "model"]
        ):
            return "machine-learning"
        else:
            return "general"

    def analyze(self, pdf_path: str) -> Dict[str, any]:
        """
Анализ PDF-документов

        Args:
pdf_path: путь к PDF-файлу

        Returns:
Словарь результатов анализа, включающий:
- домен: область исследований
- title: название статьи
- core_concepts: список основных концепций.
- пререквизиты: список необходимых знаний
- Learning_difficulty: сложность обучения
- Assessment_weeks: примерное количество учебных недель.
        """
#Извлечь заголовок
        title = self._extract_title_from_path(pdf_path)

#Извлекаем текст
        try:
            text = self._extract_text_from_pdf(pdf_path)
        except IOError:
# Если PDF-файл не читается, используйте анализ на основе пути
            return {
                "domain": "general",
                "title": title,
                "core_concepts": [],
                "prerequisites": [],
"learning_difficulty": "高级",
                "estimated_weeks": 8,
            }

#Используйте LLM для углубленного анализа
        result = self._analyze_with_llm(title, text)

        return result
