import os
import json
from hello_agents import HelloAgentsLLM, SimpleAgent

from agents.agent_prompts import REPORT_AGENT_PROMPT


if __name__ == "__main__":
    llm = HelloAgentsLLM()
    report_agent = SimpleAgent(
        name="ReportAgent",
        system_prompt=REPORT_AGENT_PROMPT,
        llm=llm,
        enable_tool_calling=False
    )

    task_result = [
        {
            'task': 'Анализ предпочтений пользователей разных возрастных групп',
            'result': {
                'text': 'Средняя сумма покупок по возрастным группам близка и составляет 58–61. По категориям товаров все возрастные группы чаще всего выбирают одежду (Clothing) — около 44–46%; на втором месте аксессуары (Accessories) — около 29–34%; обувь (Footwear) и верхняя одежда (Outerwear) встречаются реже. Пользователи 20–30 лет чаще выбирают аксессуары, 40–50 лет — обувь, подростки (<20) и пожилые (60+) относительно чаще выбирают верхнюю одежду.',
                'visualization_url': ['figures/age_group_distribution.png', 'figures/average_spending_by_age_group.png', 'figures/category_preference_by_age_group.png']
            }
        }
    ]

    print(f"\nРезультат задачи: {task_result}")

    final_result = report_agent.run(json.dumps(task_result, ensure_ascii=False))

    # Очистка отчёта: начинать с "# Резюме"
    if "# Резюме" in final_result:
        # Поиск позиции "# Резюме"
        start_idx = final_result.find("# Резюме")
        final_result = final_result[start_idx:]

    print(f"\nИтоговый аналитический отчёт: \n{final_result}")

    # Сохранение отчёта в файл
    os.makedirs("out", exist_ok=True)
    with open("out/analysis_report.md", "w", encoding="utf-8") as f:
        f.write(final_result)
