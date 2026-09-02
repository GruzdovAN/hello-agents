# agents/summary_agent.py
"""Агент оценки прогресса в обучении — создание сводок и предложений по обучению"""

from hello_agents import SimpleAgent, HelloAgentsLLM
from core.file_manager import FileManager
from pathlib import Path


class SummaryAgent(SimpleAgent):
    """
Эксперт по оценке прогресса в обучении

Функция:
    - 读取学习目标（plan.md）
- Прочитать полученные знания (knowledge_summary.md)
- Ознакомиться с процессом обучения (session_summary.md)
- Генерация оценки текущего уровня
- Рекомендовать следующий учебный контент
    """

    def __init__(self, llm: HelloAgentsLLM, file_manager: FileManager, streaming: bool = None):
        """
Инициализировать СуммарныйАгент

        Args:
llm: экземпляр HelloAgentsLLM
file_manager: экземпляр FileManager
потоковая передача: включать ли потоковую передачу (Нет = определяется автоматически)
        """
        system_prompt = """
Вы являетесь экспертом в области оценки обучения.

Задача:
1. Сравните цели обучения и текущую ситуацию и оцените мастерство (в процентах).
2. Определите сильные и слабые стороны
3. Порекомендуйте следующий учебный контент.
4. Предоставьте конкретные предложения по изучению

Выходной формат:
# 📊 Отчет о ходе обучения

## Текущий уровень
- Общее мастерство: XX%
- На этапе: Новичок/Опыт/Мастерство

## ✅ Овладейте хорошими очками знаний
- [Точка знаний 1]: Краткая оценка
- [Точка знаний 2]: Краткая оценка

## ⚠️ Очки знаний, которые необходимо усилить
- [Точка знаний 1]: Анализ причин
- [Точка знаний 2]: Анализ причин

## 📌Предложения для следующего этапа обучения
1. [Конкретная тема 1]: Рекомендации по обучению
2. [Конкретная тема 2]: Рекомендации по обучению

## 💡 Общие рекомендации
[Поощрение и руководство]
"""

        self.llm = llm
        self.file_manager = file_manager

# Добавить поддержку потокового вывода
        from utils.streaming import should_stream
        self.streaming = should_stream(streaming)

# Инициализируем, используя родительский класс
        super().__init__("SummaryAgent", llm, system_prompt)

    def run(self, domain: str) -> str:
        """
Создание сводки о ходе обучения

        Args:
домен: доменное имя

        Returns:
отчет о ходе обучения
        """
# Проверяем, существует ли область
        if not self.file_manager.domain_exists(domain):
            return f"❌ 领域 '{domain}' 不存在。请先使用 /create 创建学习计划。"

# Прочитать необходимые файлы
        try:
#Читать план обучения
            plan = self.file_manager.read_plan(domain)

# Прочитать сводку знаний
            knowledge_summary_path = (
                self.file_manager.BASE_DIR / domain / "knowledge" / "knowledge_summary.md"
            )
            if knowledge_summary_path.exists():
                knowledge_summary = knowledge_summary_path.read_text(encoding="utf-8")
            else:
Knowledge_summary = "Пока нет заметок по знаниям"

# Прочитать сводку сеанса
            session_summary_path = (
                self.file_manager.BASE_DIR / domain / "sessions" / "session_summary.md"
            )
            if session_summary_path.exists():
                session_summary = session_summary_path.read_text(encoding="utf-8")
            else:
session_summary = "Пока нет записей об обучении"

        except Exception as e:
return f"❌ Не удалось прочитать файл: {e}"

# Создать сводку
user_prompt = f"""Проанализируйте следующую учебную ситуацию:

【Цели обучения】
{plan[:2000]}

【Знания уже освоены】
{knowledge_summary[:2000]}

【Процесс обучения】
{session_summary[:2000]}

Создайте отчет о ходе обучения в соответствии с форматом слов системной подсказки.
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个学习评估专家，擅长分析学习进度并提供针对性建议。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            if self.streaming:
                from utils.streaming import stream_response
                return stream_response(self.llm, messages)
            else:
                return self.llm.invoke(messages).strip()
        except Exception as e:
# Если вызов LLM не удался, верните упрощенную версию
return f"""# 📊 Отчет о ходе обучения

## Текущий уровень
- Домен: {домен}
- Статус: в процессе обучения

## 📚 Учебный контент
- План исследования: создан
- 知识笔记：{'有' if knowledge_summary != '暂无知识笔记' else '无'}
- 学习记录：{'有' if session_summary != '暂无学习记录' else '无'}

## 💡 Предложения
Пожалуйста, продолжайте добавлять заметки и участвовать в интерактивном обучении для более точной оценки прогресса.

⚠️ Проблема с созданием подробного отчета: {e}
"""
