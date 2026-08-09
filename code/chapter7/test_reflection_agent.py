# test_reflection_agent.py
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM
from my_reflection_agent import MyReflectionAgent

load_dotenv()
llm = HelloAgentsLLM()

# Использовать универсальное слово-подсказку по умолчанию
general_agent = MyReflectionAgent(name="мой помощник по отражению", llm=llm)

# Используйте собственный код для создания слов-подсказок (аналогично главе 4).
code_prompts = {
    "initial": "Вы эксперт Python, напишите функцию: {task}",
    "reflect": "Пожалуйста, проверьте код на предмет алгоритмической эффективности:\nЗадача: {task}\nКод: {content}",
    "refine": "Пожалуйста, оптимизируйте код на основе отзывов:\nЗадача: {task}\nОбратная связь: {feedback}"
}
code_agent = MyReflectionAgent(
    name="Мой помощник по генерации кода",
    llm=llm,
    custom_prompts=code_prompts
)

# Тестовое использование
result = general_agent.run("Напишите небольшую статью о развитии искусственного интеллекта.")
print(f"Конечный результат: {result}")