"""
Глава 12. Пример 5: Быстрый старт GAIA

Соответствующий документ: 12.3.5 Реализация оценки GAIA в HelloAgents — метод 1.

Это самый простой метод оценки GAIA, и оценка завершается одной строкой кода.

ВАЖНОЕ ПРИМЕЧАНИЕ:
1. GAIA — это набор данных с ограниченным доступом, и вам необходимо сначала подать заявку на разрешение доступа к HuggingFace.
2. Необходимо установить переменную среды HF_TOKEN.
3. Необходимо использовать официальные слова подсказки системы GAIA.
"""

import os
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import GAIAEvaluationTool

# Официальное системное слово GAIA (необходимо использовать)
GAIA_SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].
YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.
If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise.
If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise.
If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string."""

# 1. Установите токен HuggingFace (если еще не установлен)
# os.environ["HF_TOKEN"] = "your_huggingface_token_here"

# 2. Создайте агента (необходимо использовать слова официальной системной подсказки GAIA)
llm = HelloAgentsLLM()
agent = SimpleAgent(
    name="TestAgent",
    llm=llm,
    system_prompt=GAIA_SYSTEM_PROMPT  # Необходимо использовать официальные слова-подсказки.
)

# 3. Создайте инструмент оценки GAIA.
gaia_tool = GAIAEvaluationTool()

# 4. Запустите оценку
results = gaia_tool.run(
    agent=agent,
    level=1,              # Уровень оценки (1=легкий, 2=средний, 3=сложный)
    max_samples=2,        # Количество оценочных образцов (0 означает все)
    export_results=True,  # Экспортируйте результаты в официальный формат GAIA.
    generate_report=True  # Создание подробных отчетов
)

# 5. Просмотр результатов
print(f"\nРезультаты оценки:")
print(f"Точный коэффициент соответствия: {results['exact_match_rate']:.2%}")
print(f"Частичный коэффициент соответствия: {results['partial_match_rate']:.2%}")
print(f"Правильный номер: {results['correct_samples']}/{results['total_samples']}")

# Пример вывода запуска:
# ============================================================
# Оценка GAIA в один клик
# ============================================================
# 
# Конфигурация:
#    Агент: ТестАгент
#    Уровень: Уровень 1
#    Количество образцов: 2
# 
# ✅ Загрузка набора данных GAIA завершена
#    Источник данных: gaia-benchmark/GAIA.
#    Сегментация: проверка
#    Уровень: 1
#    Количество образцов: 2
# 
# Прогресс оценки: 100%|██████████| 2/2 [00:10<00:00, 5,23 с/выборка]
# 
# ✅ Оценка завершена
#    Общее количество образцов: 2
#    Количество правильных образцов: 2
#    Точный коэффициент совпадения: 100,00%
#    Частичный коэффициент совпадения: 100,00%
# 
# ✅ Результаты экспортированы в ./evaluation_results/gaia_submission.json.
# ✅ Отчет создан по адресу ./evaluation_results/gaia_report.md.
# 
# Результаты оценки:
# Точный коэффициент совпадения: 100,00%
# Частичный коэффициент совпадения: 100,00%
# Правильный номер: 2/2.

