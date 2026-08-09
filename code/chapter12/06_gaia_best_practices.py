"""
Глава 12. Пример 6: Передовой опыт оценки GAIA

Соответствующий документ: 12.3.9 Передовой опыт оценки GAIA.

В этом примере демонстрируются лучшие практики оценки GAIA, в том числе:
1. Градуированная оценка
2. Быстрое тестирование небольших образцов.
3. Интерпретация результатов
"""

import os
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import GAIAEvaluationTool

# Слова подсказки официальной системы GAIA
GAIA_SYSTEM_PROMPT = """You are a general AI assistant. I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].
YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.
If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise.
If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise.
If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string."""

# Создать агента
llm = HelloAgentsLLM()
agent = SimpleAgent(
    name="TestAgent",
    llm=llm,
    system_prompt=GAIA_SYSTEM_PROMPT
)

# Создание инструментов оценки
gaia_tool = GAIAEvaluationTool()

# ============================================================
# Лучшая практика 1: Поэтапное оценивание
# ============================================================
print("="*60)
print("Лучшая практика 1: Поэтапное оценивание")
print("="*60)

# Шаг 1: Уровень оценки 1 (простое задание)
print("\nШаг 1: Уровень оценки 1 (простая задача)")
results_l1 = gaia_tool.run(agent, level=1, max_samples=10)
print(f"Коэффициент точного соответствия уровня 1: {results_l1['exact_match_rate']:.2%}")

# Шаг 2. Если уровень 1 показал хорошие результаты, оцените уровень 2.
if results_l1['exact_match_rate'] > 0.6:
    print("\nШаг 2: Уровень оценки 2 (средние задачи)")
    results_l2 = gaia_tool.run(agent, level=2, max_samples=10)
    print(f"Коэффициент точного соответствия уровня 2: {results_l2['exact_match_rate']:.2%}")
    
    # Шаг 3. Если уровень 2 работает хорошо, оцените уровень 3.
    if results_l2['exact_match_rate'] > 0.4:
        print("\nШаг 3: Уровень оценивания 3 (сложные задания)")
        results_l3 = gaia_tool.run(agent, level=3, max_samples=10)
        print(f"Коэффициент точного соответствия уровня 3: {results_l3['exact_match_rate']:.2%}")
    else:
        print("\n⚠️ Уровень 2 работает плохо, рекомендуется сначала оптимизировать, а затем оценивать уровень 3.")
else:
    print("\n⚠️ Уровень 1 работает плохо. Рекомендуется сначала оптимизировать, а затем оценивать более высокие уровни.")

# ============================================================
# Лучшая практика 2: Быстрое тестирование на небольших выборках
# ============================================================
print("\n" + "="*60)
print("Лучшая практика 2: Быстрое тестирование на небольших выборках")
print("="*60)

# Быстрый тест (2 образца на уровень)
for level in [1, 2, 3]:
    print(f"\nБыстрый тест уровня {уровень}:")
    results = gaia_tool.run(agent, level=level, max_samples=2)
    print(f"  Точный коэффициент соответствия: {results['exact_match_rate']:.2%}")

# ============================================================
# Передовая практика 3: Интерпретация результатов
# ============================================================
print("\n" + "="*60)
print("Передовая практика 3: Интерпретация результатов")
print("="*60)

def interpret_results(level, exact_match_rate):
    """Интерпретация результатов оценки"""
    print(f"\nLevel {уровень} Интерпретация результата:")
    print(f"Точный коэффициент соответствия: {exact_match_rate:.2%}")
    
    if level == 1:
        if exact_match_rate >= 0.6:
            print("✅ Отлично – уверенные базовые способности")
        elif exact_match_rate >= 0.4:
            print("⚠️ Хорошо — доступны базовые способности.")
        else:
            print("❌ Плохо – требует улучшения")
            print("предположение:")
            print("  - Проверьте, содержит ли слово системной подсказки официальные требования формата GAIA.")
            print("  - Проверьте правильность логики извлечения ответа.")
            print("  - Проверьте, достаточно ли мощна модель LLM.")
    
    elif level == 2:
        if exact_match_rate >= 0.4:
            print("✅ Отлично - Умеренно способен к выполнению задач.")
        elif exact_match_rate >= 0.2:
            print("⚠️ Хорошо — доступны средние возможности выполнения миссий.")
        else:
            print("❌ Плохо – требует улучшения")
            print("предположение:")
            print("  - Расширение возможностей многоэтапного рассуждения")
            print("  - Увеличение возможностей использования инструмента")
            print("  - Оптимизировать построение цепочки рассуждений")
    
    elif level == 3:
        if exact_match_rate >= 0.2:
            print("✅ Отлично – сильные способности в сложных задачах.")
        elif exact_match_rate >= 0.1:
            print("⚠️ Хорошо — доступны сложные задачи")
        else:
            print("❌ Плохо – требует улучшения")
            print("предположение:")
            print("  - Совершенствовать навыки сложного рассуждения.")
            print("  - Добавлены возможности обработки длинного контекста.")
            print("  - Оптимизировать совместное использование цепочек инструментов.")

# Интерпретируйте результаты
if 'results_l1' in locals():
    interpret_results(1, results_l1['exact_match_rate'])
if 'results_l2' in locals():
    interpret_results(2, results_l2['exact_match_rate'])
if 'results_l3' in locals():
    interpret_results(3, results_l3['exact_match_rate'])

# ============================================================
# Анализ прогресса сложности
# ============================================================
print("\n" + "="*60)
print("Анализ прогресса сложности")
print("="*60)

if 'results_l1' in locals() and 'results_l2' in locals():
    if results_l1['exact_match_rate'] > results_l2['exact_match_rate']:
        print("✅ Нормальный прогресс: Уровень 1 > Уровень 2.")
    else:
        print("⚠️ Аномальная ситуация: Уровень 2 >= Уровень 1 (может быть отклонение набора данных или характеристики агента)")

if 'results_l2' in locals() and 'results_l3' in locals():
    if results_l2['exact_match_rate'] > results_l3['exact_match_rate']:
        print("✅ Нормальный прогресс: Уровень 2 > Уровень 3.")
    else:
        print("⚠️ Аномальная ситуация: Уровень 3 >= Уровень 2 (может быть отклонение набора данных или характеристики агента)")

