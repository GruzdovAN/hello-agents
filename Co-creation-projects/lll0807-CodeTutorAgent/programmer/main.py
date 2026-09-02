import os
import sys
from dotenv import load_dotenv
from hello_agents.core.llm import HelloAgentsLLM
from services.knowledge import LearningKnowledgeService

# Инициализация Tutor (автоматически создаёт все подагенты)
from agents.tutor import TutorAgent

load_dotenv()

if "src" not in sys.path:
    sys.path.append(os.path.abspath("src"))

# Инициализация LLM
llm = HelloAgentsLLM()

print("✅ Конфигурация окружения завершена")
print("✅ LLM инициализирован")

print("Создание интеллектуального наставника по программированию...")
knowledge = LearningKnowledgeService(user_id="1")
tutor = TutorAgent(llm, knowledge)

while True:
    user_goal = input("Введите запрос: ")
    # Хочу изучить list comprehensions в Python
    # Хочу обновить план обучения
    print(f"Цель пользователя: {user_goal}\n")

    # Tutor вызывает инструмент call_planner
    response = tutor.run(f"Пользователь сказал: '{user_goal}'.")

    print("=== Ответ Tutor ===")
    print(response)
