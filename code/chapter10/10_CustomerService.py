"""
10.3.4 Использование инструментов A2A в агентах
(2) Практический пример: интеллектуальная система обслуживания клиентов.
"""

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import A2ATool
from hello_agents.protocols import A2AServer
import threading
import time
from dotenv import load_dotenv

load_dotenv()
llm = HelloAgentsLLM()

# 1. Создайте службу технического эксперта-агента.
tech_expert = A2AServer(
    name="tech_expert",
    description="Технические эксперты ответят на технические вопросы"
)

@tech_expert.skill("answer")
def answer_tech_question(text: str) -> str:
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text
    # В реальных приложениях здесь будет вызываться LLM или база знаний.
    return f"Технический ответ: Что касается «{вопроса}», я рекомендую вам ознакомиться с нашей технической документацией..."

# 2. Создать службу агента-консультанта по продажам.
sales_advisor = A2AServer(
    name="sales_advisor",
    description="Продавец-консультант, ответит на вопросы по продажам"
)

@sales_advisor.skill("answer")
def answer_sales_question(text: str) -> str:
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text
    return f"Ответ продавца: Что касается «{question}», у нас есть специальное предложение..."

# 3. Запустите службу
threading.Thread(target=lambda: tech_expert.run(port=6000), daemon=True).start()
threading.Thread(target=lambda: sales_advisor.run(port=6001), daemon=True).start()
time.sleep(2)

# 4. Создайте агента администратора (используя SimpleAgent HelloAgents).
receptionist = SimpleAgent(
    name="Регистратор",
    llm=llm,
    system_prompt="""Вы - администратор службы поддержки клиентов, ответственный за:
1. Проанализируйте тип проблемы клиента (техническая проблема или проблема с продажами).
2. Передайте вопрос соответствующему эксперту.
3. Сопоставьте ответы экспертов и верните их заказчику

Пожалуйста, оставайтесь вежливыми и профессиональными."""
)

# Добавьте технические экспертные инструменты
tech_tool = A2ATool(
    agent_url="http://localhost:6000",
    name="tech_expert",
    description="Технические эксперты ответят на вопросы, связанные с технологиями"
)
receptionist.add_tool(tech_tool)

# Добавьте инструменты консультанта по продажам
sales_tool = A2ATool(
    agent_url="http://localhost:6001",
    name="sales_advisor",
    description="Продавец-консультант ответит на вопросы о цене и покупке"
)
receptionist.add_tool(sales_tool)

# 5. Обработка запросов клиентов
def handle_customer_query(query):
    print(f"\nЗапрос клиента: {query}")
    print("=" * 50)
    response = receptionist.run(query)
    print(f"\nОтвет службы поддержки: {response}")
    print("=" * 50)

# Тестируйте разные типы вопросов
if __name__ == "__main__":
    handle_customer_query("Как вызвать ваш API?")
    handle_customer_query("Сколько стоит Enterprise Edition?")
    handle_customer_query("Как я могу интегрировать его в свой проект Python?")

