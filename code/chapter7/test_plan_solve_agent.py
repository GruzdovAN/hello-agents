# test_plan_solve_agent.py
from dotenv import load_dotenv
from hello_agents.core.llm import HelloAgentsLLM
from my_plan_solve_agent import MyPlanAndSolveAgent

# Загрузить переменные среды
load_dotenv()

# Создать экземпляр LLM
llm = HelloAgentsLLM()

# Создайте собственный PlanAndSolveAgent.
agent = MyPlanAndSolveAgent(
    name="Мой помощник по планированию",
    llm=llm
)

# Тестируйте сложные проблемы
question = "В понедельник фруктовый магазин продал 15 яблок. Во вторник было продано вдвое больше яблок, чем в понедельник. В среду было продано на 5 меньше, чем во вторник. Сколько всего яблок было продано за последние три дня?"

result = agent.run(question)
print(f"\nОкончательный результат: {result}")

# Просмотреть историю разговоров
print(f"История разговоров: {len(agent.get_history())} сообщений")