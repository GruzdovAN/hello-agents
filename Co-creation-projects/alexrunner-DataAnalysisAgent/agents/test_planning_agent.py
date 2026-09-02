from hello_agents import HelloAgentsLLM

from agents.react_agent import NewReActAgent
from agents.agent_prompts import PLAN_AGENT_PROMPT
from tools.data_exploration import create_data_exploration_registry


if __name__ == "__main__":
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
