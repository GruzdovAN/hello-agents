import os
import json
import shutil
from hello_agents import HelloAgentsLLM, SimpleAgent

from agents.react_agent import NewReActAgent
from agents.agent_prompts import PLAN_AGENT_PROMPT, ANALYSIS_AGENT_PROMPT, REPORT_AGENT_PROMPT
from tools.data_exploration import create_data_exploration_registry
from tools.data_analysis import create_data_analysis_registry


if __name__ == "__main__":
    # Очистка каталога out
    if os.path.exists("out"):
        shutil.rmtree("out")
    os.makedirs("out", exist_ok=True)
    os.makedirs("out/figures", exist_ok=True)

    llm = HelloAgentsLLM()
    registry = create_data_exploration_registry()
    planning_agent = NewReActAgent(
        name="PlanningAgent",
        llm=llm,
        custom_prompt=PLAN_AGENT_PROMPT,
        tool_registry=registry,
        max_steps=5
    )

    question = "Начните анализ"
    try:
        plan_result = planning_agent.run(question)
        print(f"Планирование задач: {plan_result}")
    except Exception as e:
        print(f"Ошибка при выполнении: {e}")

    # Проверка, что plan_result — список Python
    if not isinstance(plan_result, list):
        print("Ошибка: результат планирования имеет неверный формат, ожидается список Python.")
        exit(1)

    registry = create_data_analysis_registry()
    analysis_agent = NewReActAgent(
        name="AnalysisAgent",
        llm=llm,
        custom_prompt=ANALYSIS_AGENT_PROMPT,
        tool_registry=registry,
        max_steps=5
    )

    task_result = []

    for task in plan_result:
        print(f"Выполнение задачи: {task}")
        try:
            answer = analysis_agent.run(task)
            task_result.append({ "task": task, "result": answer })
            print(f"Результат задачи: {answer}")
        except Exception as e:
            print(f"Ошибка при выполнении: {e}")

    print(f"\nРезультаты всех задач: {task_result}")

    report_agent = SimpleAgent(
        name="ReportAgent",
        system_prompt=REPORT_AGENT_PROMPT,
        llm=llm,
        enable_tool_calling=False
    )

    final_result = report_agent.run(json.dumps(task_result, ensure_ascii=False))

    # Очистка отчёта: начинать с "# Резюме"
    if "# Резюме" in final_result:
        start_idx = final_result.find("# Резюме")
        final_result = final_result[start_idx:]

    print(f"\nИтоговый аналитический отчёт: \n{final_result}")

    # Сохранение отчёта в файл
    os.makedirs("out", exist_ok=True)
    with open("out/analysis_report.md", "w", encoding="utf-8") as f:
        f.write(final_result)
