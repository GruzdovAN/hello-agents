"""
Протокол A2A + вариант интеграции HelloAgents SimpleAgent

Покажите, как интегрировать Агент протокола A2A в SimpleAgent как инструмент.
"""

from hello_agents.protocols import A2AServer, A2AClient
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import ToolRegistry, Tool, ToolParameter
import threading
import time
from typing import Dict, Any

# ============================================================
# 1. Создайте профессиональную службу агента A2A.
# ============================================================

# Технический экспертный агент
tech_expert = A2AServer(
    name="tech_expert",
    description="Технические эксперты ответят на вопросы, связанные с технологиями",
    version="1.0.0"
)

@tech_expert.skill("answer")
def answer_tech_question(text: str) -> str:
    """Отвечу на технические вопросы"""
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text
    
    print(f"  [Технический эксперт] Ответ на вопрос: {question}")
    return f"Технический ответ: Что касается «{question}», это профессиональный ответ на технический вопрос..."

# агент-консультант по продажам
sales_advisor = A2AServer(
    name="sales_advisor",
    description="Продавец-консультант, ответит на вопросы по продажам",
    version="1.0.0"
)

@sales_advisor.skill("answer")
def answer_sales_question(text: str) -> str:
    """Отвечать на вопросы по продажам"""
    import re
    match = re.search(r'answer\s+(.+)', text, re.IGNORECASE)
    question = match.group(1).strip() if match else text
    
    print(f"  [Продавец-консультант] Ответ на вопрос: {question}")
    return f"Ответ продавца: Что касается «{question}», у нас есть специальное предложение..."

# ============================================================
# 2. Запустите службу агента A2A.
# ============================================================

print("="*60)
print("🚀 Запустите услуги профессионального агента")
print("="*60)

threading.Thread(target=lambda: tech_expert.run(port=6000), daemon=True).start()
threading.Thread(target=lambda: sales_advisor.run(port=6001), daemon=True).start()

print("✓ Агент технического эксперта запускается по адресу http://localhost:6000.")
print("✓ Агент-консультант по продажам начинается с адреса http://localhost:6001.")

print("\n⏳ Ожидание запуска службы...")
time.sleep(3)

# ============================================================
# 3. Создайте инструмент A2A (инкапсулируйте агент A2A как инструмент).
# ============================================================

class A2ATool(Tool):
    """Инкапсулируйте агент A2A в инструмент HelloAgents"""

    def __init__(self, name: str, description: str, agent_url: str, skill_name: str = "answer"):
        self.agent_url = agent_url
        self.skill_name = skill_name
        self.client = A2AClient(agent_url)
        self._name = name
        self._description = description
        self._parameters = [
            ToolParameter(
                name="question",
                type="string",
                description="Вопросы, которые стоит задать",
                required=True
            )
        ]

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_parameters(self) -> list[ToolParameter]:
        """Получить параметры инструмента"""
        return self._parameters

    def run(self, **kwargs) -> str:
        """Инструмент выполнения"""
        question = kwargs.get('question', '')
        result = self.client.execute_skill(self.skill_name, f"answer {question}")
        if result.get('status') == 'success':
            return result.get('result', 'No response')
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

# Создание инструментов
tech_tool = A2ATool(
    name="tech_expert",
    description="Технические эксперты ответят на вопросы, связанные с технологиями",
    agent_url="http://localhost:6000"
)

sales_tool = A2ATool(
    name="sales_advisor",
    description="Продавец-консультант ответит на вопросы, связанные с продажами",
    agent_url="http://localhost:6001"
)

# ============================================================
# 4. Создайте SimpleAgent (с помощью инструментов A2A)
# ============================================================

print("\n" + "="*60)
print("🤖 Создать секретаршу SimpleAgent")
print("="*60)

# Инициализировать LLM
llm = HelloAgentsLLM()

# Создать агента-секретаря
receptionist = SimpleAgent(
    name="Регистратор",
    llm=llm,
    system_prompt="""Вы - администратор службы поддержки клиентов, ответственный за:
1. Проанализируйте тип проблемы клиента (техническая проблема или проблема с продажами).
2. Используйте соответствующий инструмент (tech_expert или sales_advisor), чтобы получить ответ.
3. Систематизируйте ответы и верните их клиенту.

Доступные инструменты:
- tech_expert: отвечайте на технические вопросы
- sales_advisor: отвечать на вопросы о продажах

Пожалуйста, оставайтесь вежливыми и профессиональными."""
)

# Добавьте инструменты A2A
receptionist.add_tool(tech_tool)
receptionist.add_tool(sales_tool)

print("✓ Агент администратора создан.")
print("✓ Интегрированные инструменты A2A: tech_expert, sales_advisor")

# ============================================================
# 5. Протестируйте интегрированную систему
# ============================================================

print("\n" + "="*60)
print("🧪 Тестирование интеграции A2A + SimpleAgent")
print("="*60)

# тестовые вопросы
test_questions = [
    "Есть ли акции на вашу продукцию?",
    "Как настроить SSL-сертификат сервера?",
    "хотелось бы узнать о тарифном плане"
]

for i, question in enumerate(test_questions, 1):
    print(f"\nВопрос {i}: {вопрос}")
    print("-" * 60)

    try:
        # Используйте метод запуска SimpleAgent.
        response = receptionist.run(question)
        print(f"Ответ: {ответ}")
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

    print()

# ============================================================
# 6. Поддерживайте работу служб
# ============================================================

print("="*60)
print("💡 Система все еще работает")
print("="*60)
print("Вы можете продолжить тестирование или нажать Ctrl+C, чтобы остановить\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n ✅ Система остановлена")

