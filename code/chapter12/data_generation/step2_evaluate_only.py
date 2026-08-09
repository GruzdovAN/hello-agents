"""
Шаг 2. Оценивайте только сгенерированные вопросы AIME.

Как запустить:
python data_generation/step2_evaluate_only.py <сгенерированный_путь_данных>

Параметры:
-generated_data_path: путь к сгенерированным данным.

Описание:
- Используйте реальные вопросы AIME 2025 в качестве справочного материала.
- Источник набора данных: math-ai/aime25 (формат JSONL).

Пример:
python data_generation/step2_evaluate_only.py data_ogenic/generated_data/aime_generated_20251011_042741.json
"""

import json
import os
import sys
from datetime import datetime
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import LLMJudgeTool, WinRateTool


def run_evaluation(generated_data_path: str):
    """
    Запустите процесс оценки

    Аргументы:
        сгенерированный_данный_путь: путь к сгенерированным данным
    """
    print("\n" + "="*80)
    print("🎯 Шаг 2. Оцените сгенерированные вопросы AIME.")
    print("="*80)
    print(f"\nИнформация о конфигурации:")
    print(f"  – Сгенерированные данные: {generated_data_path}")
    print(f"  - Справочник по оценке: реальные тестовые вопросы AIME 2025.")
    
    # Проверьте, существует ли файл
    if not os.path.exists(generated_data_path):
        print(f"\n❌ Ошибка: файл не существует: {generated_data_path}")
        return
    
    # Загрузите сгенерированные данные, чтобы получить количество вопросов.
    with open(generated_data_path, 'r', encoding='utf-8') as f:
        generated_data = json.load(f)
    num_problems = len(generated_data)
    print(f"  - Количество вопросов: {num_problems}")
    
    # Создать каталог результатов оценивания
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evaluation_dir = f"data_generation/evaluation_results/{timestamp}"
    os.makedirs(evaluation_dir, exist_ok=True)
    os.makedirs(os.path.join(evaluation_dir, "llm_judge"), exist_ok=True)
    os.makedirs(os.path.join(evaluation_dir, "win_rate"), exist_ok=True)

    # Создать LLM
    llm = HelloAgentsLLM()

    # # ========== Оценка судьи LLM ==========
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

    # ========== Оценка процента побед ==========
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
    
    # ========== Создать подробный отчет ==========
    comprehensive_report_path = None
    if llm_judge_result or win_rate_result:
        print("\n" + "="*80)
        print("📊 Шаг 2.3: Создайте подробный отчет")
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
    print("🎉Процесс оценки завершен!")
    print("="*80)
    print(f"\n📁 Выходной файл:")
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
        print("Использование: python Step2_evaluate_only.py <сгенерированный_путь_данных>")
        print("\nОписание:")
        print("  - Используйте реальные вопросы AIME 2025 в качестве справочного материала.")
        print("  - Источник набора данных: math-ai/aime25 (формат JSONL).")
        print("  - Требуется установка: pip install pandas pyarrow datasets.")
        print("\nПример:")
        print("python step2_evaluate_only.py data_generation/generated_data/aime_generated_20251011_042741.json")
        sys.exit(1)

    generated_data_path = sys.argv[1]

    run_evaluation(generated_data_path)


if __name__ == "__main__":
    main()

