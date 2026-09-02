from hello_agents import HelloAgentsLLM

from agents.react_agent import NewReActAgent
from agents.agent_prompts import ANALYSIS_AGENT_PROMPT
from tools.data_analysis import create_data_analysis_registry


if __name__ == "__main__":
    llm = HelloAgentsLLM()
    registry = create_data_analysis_registry()
    analysis_agent = NewReActAgent(
        name="AnalysisAgent",
        llm=llm,
        custom_prompt=ANALYSIS_AGENT_PROMPT,
        tool_registry=registry,
        max_steps=5
    )

    plan_result = ["Анализ предпочтений пользователей разных возрастных групп"]
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
