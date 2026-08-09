"""
Пример интеграции ContextBuilder и Агента

Показывает, как интегрировать ContextBuilder в агент для достижения:
1. Контекстно-зависимый агент
2. Автоматически создавать оптимизированный контекст.
3. Совместная работа по управлению памятью и построению контекста.
"""
from dotenv import load_dotenv
load_dotenv()
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.context import ContextBuilder, ContextConfig
#from hello_agents.tools import MemoryTool, RAGTool
from hello_agents.core.message import Message
from datetime import datetime


class ContextAwareAgent(SimpleAgent):
    """Контекстно-зависимый агент"""

    def __init__(self, name: str, llm: HelloAgentsLLM, **kwargs):
        super().__init__(name=name, llm=llm, **kwargs)

        
        #（Optional）
        # self.memory_tool = MemoryTool(user_id=kwargs.get("user_id", "default")) 
        # self.rag_tool = RAGTool(knowledge_base_path=kwargs.get("knowledge_base_path", "./kb"))

        # Инициализировать построитель контекста
        self.context_builder = ContextBuilder(
            # memory_tool=self.memory_tool,
            # rag_tool=self.rag_tool,
            config=ContextConfig(max_tokens=4000)
        )

        self.conversation_history = []

    def run(self, user_input: str) -> str:
        """Запустите агент для автоматического создания оптимизированного контекста."""

        # 1. Используйте ContextBuilder для создания оптимизированного контекста.
        optimized_context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self.system_prompt
        )

        # 2. Вызовите LLM, используя оптимизированный контекст.
        messages = [
            {"role": "system", "content": optimized_context},
            {"role": "user", "content": user_input}
        ]
        response = self.llm.invoke(messages).content

        # 3. Обновить историю разговоров
        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # 4. Запишите важные взаимодействия в систему памяти.
        # self.memory_tool.run({
        #     "action": "add",
        #     "content": f"Q: {user_input}\nA: {response[:200]}...", # Резюме
        #     "memory_type": "episodic",
        #     "importance": 0.6
        # })

        return response


def main():
    print("=" * 80)
    print("Пример интеграции ContextBuilder и Агента")
    print("=" * 80 + "\n")

    # Настроить LLM
    from hello_agents.core.llm import HelloAgentsLLM
    llm = HelloAgentsLLM()

    # Пример использования
    agent = ContextAwareAgent(
        name="Консультант по анализу данных",
        llm=llm,
        system_prompt="Вы старший консультант по разработке данных Python."
    )

    # поговорить
    response = agent.run("Как оптимизировать использование памяти Pandas?")
    print(f"Ассистент ответил:\n{response}\n")

    # продолжить разговор
    response = agent.run("Можете ли вы привести конкретный пример кода?")
    print(f"Ассистент ответил:\n{response}\n")

    print("=" * 80)


if __name__ == "__main__":
    main()
