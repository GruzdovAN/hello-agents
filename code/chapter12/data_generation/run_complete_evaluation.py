"""
Полный процесс оценки

Запустите полный процесс создания и оценки данных:
1. Создайте вопросы AIME
2. Оценка судьи LLM
3. Оценка процента побед
4. Создавайте подробные отчеты

Как запустить:
python data_generation/run_complete_evaluation.py 30 3.0

Параметры:
- 30: количество сгенерированных вопросов.
- 3.0: Задержка между каждым поколением (секунды).

Описание:
- Используйте реальные вопросы AIME 2025 в качестве справочного материала.
- Источник набора данных: math-ai/aime25 (формат JSONL).
"""

import json
import os
import sys
from datetime import datetime
from aime_generator import AIMEGenerator
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import LLMJudgeTool, WinRateTool


def run_complete_evaluation(
    num_problems: int = 30,
    delay_seconds: float = 3.0
):
    """
    Запустите полный процесс оценки

    Аргументы:
        num_problems: количество сгенерированных вопросов
        задержание_секунд: задержка в секундах между каждой сборкой, чтобы избежать ограничений скорости API.
    """
    print("\n" + "="*80)
    print("🚀 Полный процесс генерации и оценки данных AIME")
    print("="*80)
    print(f"\nИнформация о конфигурации:")
    print(f"  – Количество созданных вопросов: {num_problems}")
    print(f"  - Задержка API: {delay_секунды} секунд/вопрос.")
    print(f"  - Генерация справочных данных: TianHongZXY/aime-1983-2025 (более 900 вопросов)")
    print(f"  - Справочник по оценке: реальные тестовые вопросы AIME 2025.")

    # ========== Шаг 1. Создайте вопросы AIME ==========
    print("\n" + "="*80)
    print("📝 Шаг 1. Создайте вопросы AIME.")
    print("="*80)

    generator = AIMEGenerator(delay_seconds=delay_seconds)
    generated_data_path = generator.generate_and_save(
        num_problems=num_problems,
        output_dir="data_generation/generated_data"
    )

    print(f"\n ✅ Шаг 1 завершен! Сгенерированные данные сохраняются в: {generated_data_path}.")

    # ========== Шаг 2: Оценка ==========
    # Создать каталог результатов оценивания
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evaluation_dir = f"data_generation/evaluation_results/{timestamp}"
    os.makedirs(evaluation_dir, exist_ok=True)
    os.makedirs(os.path.join(evaluation_dir, "llm_judge"), exist_ok=True)
    os.makedirs(os.path.join(evaluation_dir, "win_rate"), exist_ok=True)

    # Создать LLM
    llm = HelloAgentsLLM()

    # ========== Шаг 2.1: Оценка судьи LLM ==========
    print(f"\n🎯 Шаг 2.1: Оценка судьи LLM (по сравнению с AIME 2025)")

    llm_judge_result = None
    try:
        llm_judge_tool = LLMJudgeTool(llm=llm)

        llm_judge_result_json = llm_judge_tool.run({
            "generated_data_path": generated_data_path,
            "reference_year": 2025,
            "max_samples": num_problems,
            "output_dir": os.path.join(evaluation_dir, "llm_judge"),
            "judge_model": "gpt-4o"
        })

        llm_judge_result = json.loads(llm_judge_result_json)
        print(f"\n ✅ Оценка судьи LLM завершена!")
        print(f"   Средний общий балл: {llm_judge_result['metrics']['average_total_score']:.2f}/5,0")
        print(f"   Процент прохождения: {llm_judge_result['metrics']['pass_rate']:.2%}")
    except Exception as e:
        print(f"\n❌ Оценка судьи LLM не удалась: {e}")
        import traceback
        traceback.print_exc()

    # ========== Шаг 2.2: Оценка процента побед ==========
    print(f"\n🏆 Шаг 2.2: Оценка процента побед (по сравнению с AIME 2025)")

    win_rate_result = None
    try:
        win_rate_tool = WinRateTool(llm=llm)

        win_rate_result_json = win_rate_tool.run({
            "generated_data_path": generated_data_path,
            "reference_year": 2025,
            "num_comparisons": min(num_problems, 20),  # До 20 сравнений
            "output_dir": os.path.join(evaluation_dir, "win_rate"),
            "judge_model": "gpt-4o"
        })

        win_rate_result = json.loads(win_rate_result_json)
        print(f"\n ✅ Оценка процента побед завершена!")
        print(f"   Win Rate: {win_rate_result['metrics']['win_rate']:.2%}")
    except Exception as e:
        print(f"\n❌ Не удалось оценить процент побед: {e}")
        import traceback
        traceback.print_exc()

    # ========== Шаг 3: Создайте подробный отчет ==========
    comprehensive_report_path = None
    if llm_judge_result or win_rate_result:
        print("\n" + "="*80)
        print("📊 Шаг 3: Создайте подробный отчет")
        print("="*80)

        comprehensive_report_path = os.path.join(evaluation_dir, "comprehensive_report.md")

        # Создавайте подробные отчеты
        report = generate_comprehensive_report(
            generated_data_path,
            llm_judge_result,
            win_rate_result
        )

        with open(comprehensive_report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n ✅ Подробный отчет сохранен: {comprehensive_report_path}")

    # ========== Завершено ==========
    print("\n" + "="*80)
    print("🎉 Полный процесс оценки завершен!")
    print("="*80)
    print(f"\n📁 Выходной файл:")
    print(f"   – Сгенерированные данные: {generated_data_path}")
    print(f"   – Каталог результатов оценки: {evaluation_dir}.")

    if llm_judge_result:
        print(f"   - Отчет судьи LLM: {llm_judge_result.get('report_file', 'N/A')}")
    if win_rate_result:
        print(f"   - Отчет о проценте побед: {win_rate_result.get('report_file', 'N/A')}")

    if comprehensive_report_path:
        print(f"   – Подробный отчет: {comprehensive_report_path}.")

    print(f"\n💡 Следующий шаг:")
    if comprehensive_report_path:
        print(f"   1. Просмотрите подробный отчет: {comprehensive_report_path}.")
    print(f"   2. Запустите человеческую проверку: python data_generation/human_verification_ui.py {generated_data_path}")

    return {
        "generated_data_path": generated_data_path,
        "llm_judge_result": llm_judge_result,
        "win_rate_result": win_rate_result,
        "comprehensive_report_path": comprehensive_report_path
    }


def generate_comprehensive_report(
    generated_data_path: str,
    llm_judge_result: dict,
    win_rate_result: dict
) -> str:
    """Создать комплексный отчет об оценке"""

    # Загрузить сгенерированные данные
    with open(generated_data_path, 'r', encoding='utf-8') as f:
        generated_data = json.load(f)

    report = f"""# Подробный отчет о создании и оценке данных AIME

## 1. Основная информация

- **Время генерации**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Количество сгенерированных вопросов**: {len(generated_data)}
- **Справочный год AIME**: 2025 г.
- **Путь к сгенерированным данным**: {generated_data_path}

## 2. Статистика формирования данных

### Распределение тем

"""

    # Статистическое распределение тем
    topic_counts = {}
    for item in generated_data:
        topic = item.get('topic', 'Unknown')
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    report += "| Тема | Количество | Пропорция |\n"
    report += "|------|------|------|\n"
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = count / len(generated_data) * 100
        report += f"| {topic} | {count} | {percentage:.1f}% |\n"

    # Результаты судьи LLM
    if llm_judge_result:
        report += "\n## 3. Результаты оценки судьи LLM\n\n"
        report += f"""**Общая оценка**:
– Средний общий балл: {llm_judge_result['metrics']['average_total_score']:.2f}/5,0.
– Процент сдачи: {llm_judge_result['metrics']['pass_rate']:.2%}
– Отличная оценка: {llm_judge_result['metrics']['excellent_rate']:.2%}

**Рейтинги по каждому параметру**:

| Размеры | Средний балл |
|------|--------|
| Корректность | {llm_judge_result['метрики']['dimension_averages']['правильность']:.2f}/5.0 |
| Ясность | {llm_judge_result['метрики']['dimension_averages']['ясность']:.2f}/5.0 |
| Уровень сложности | {llm_judge_result['metrics']['dimension_averages']['difficulty_match']:.2f}/5.0 |
| Полнота | {llm_judge_result['метрики']['dimension_averages']['полнота']:.2f}/5.0 |

"""

    # Результаты по проценту побед
    if win_rate_result:
        report += "\n## 4. Результаты оценки процента побед\n\n"
        report += f"""**Статистика выигрышей**:
- Процент побед: {win_rate_result['metrics']['win_rate']:.2%}
- Коэффициент потерь: {win_rate_result['metrics']['loss_rate']:.2%}
- Ничья: {win_rate_result['metrics']['tie_rate']:.2%}

**Количество сравнений**:
– Общее количество сравнений: {win_rate_result['metrics']['total_comparisons']} раз.
- Количество побед: {win_rate_result['metrics']['wins']} раз.
– Количество неудач: {win_rate_result['metrics']['losses']} раз.
- Количество ничьих: {win_rate_result['metrics']['ties']} раз.

"""

    # Комплексное заключение
    report += "\n## 5. Комплексное заключение\n\n"

    if llm_judge_result and win_rate_result:
        overall_avg_score = llm_judge_result['metrics']['average_total_score']
        overall_win_rate = win_rate_result['metrics']['win_rate']

        if overall_avg_score >= 4.5 and overall_win_rate >= 0.48:
            report += "✅ **Вывод**: Качество сгенерированных данных **отличное**, достигая или превосходя уровень реальных вопросов AIME. \п"
        elif overall_avg_score >= 4.0 and overall_win_rate >= 0.45:
            report += "✅ **Вывод**: Качество сгенерированных данных **хорошее**, близкое к уровню реальных вопросов AIME. \п"
        else:
            report += "⚠️ **Вывод**: качество генерируемых данных **необходимо улучшить**, и между ними и реальными вопросами AIME все еще существует разрыв. \п"

        report += f"\n**Общие показатели**:\n"
        report += f"- Оценка судьи LLM: {overall_avg_score:.2f}/5,0\n"
        report += f"- Win Rate: {overall_win_rate:.2%}\n"

    # Предложения по улучшению
    report += "\n## 6. Предложения по улучшению\n\n"

    if llm_judge_result:
        avg_score = llm_judge_result['metrics']['average_total_score']
        if avg_score >= 4.5:
            report += "- ✅ Продолжать поддерживать текущую стратегию генерации\n"
            report += "- ✅ Вы можете рассмотреть возможность увеличения количества генерируемых \n"
        elif avg_score >= 4.0:
            report += "- 🔄 Оптимизировать слова-подсказки, генерируемые в вопросе\n"
            report += "- 🔄 Добавить этап качественной фильтрации\n"
        else:
            report += "- ⚠️ Необходимо изменить дизайн сгенерированных слов-подсказок\n"
            report += "- ⚠️ Рассмотрите возможность использования более сильных генеративных моделей\n"
            report += "- ⚠️Добавлена ​​ручная проверка\n"

    # следующие шаги
    report += "\n## 7. Следующие шаги\n\n"
    report += "1. **Проверка вручную**. Запустите интерфейс проверки вручную, чтобы просмотреть созданные вопросы вручную.\n"
    report += f"   ```bash\n   python data_generation/human_verification_ui.py {generated_data_path}\n   ```\n\n"
    report += "2. **Проверка качества**: проверка качественных вопросов на основе результатов оценки\n\n"
    report += "3. **Итеративная оптимизация**: оптимизируйте стратегию генерации на основе отзывов об оценке.\n"

    report += f"\n---\n\n*Время создания отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    return report


def main():
    if len(sys.argv) < 2:
        print("Использование: python run_complete_evaluation.py <количество_проблем> [задержка_секунд]")
        print("\nОписание:")
        print("  - Используйте реальные вопросы AIME 2025 в качестве справочного материала.")
        print("  - Источник набора данных: math-ai/aime25 (формат JSONL).")
        print("\nПример:")
        print("python run_complete_evaluation.py 30 3.0")
        sys.exit(1)

    # Анализ аргументов командной строки
    num_problems = int(sys.argv[1])
    delay_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0

    # Проведите полную оценку
    run_complete_evaluation(
        num_problems=num_problems,
        delay_seconds=delay_seconds
    )


if __name__ == "__main__":
    main()

