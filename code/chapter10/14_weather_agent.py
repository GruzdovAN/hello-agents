"""Использование сервера погоды MCP в Агенте"""

import os
from dotenv import load_dotenv
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool

load_dotenv()


def create_weather_assistant():
    """Создать помощник погоды"""
    llm = HelloAgentsLLM()

    assistant = SimpleAgent(
        name="помощник погоды",
        llm=llm,
        system_prompt="""Вы помощник погоды и можете узнать погоду в городе.
Используйте инструмент get_weather для запроса погоды, который поддерживает названия китайских городов.
"""
    )

    # Добавить инструмент погоды MCP
    server_script = os.path.join(os.path.dirname(__file__), "14_weather_mcp_server.py")
    weather_tool = MCPTool(server_command=["python", server_script])
    assistant.add_tool(weather_tool)

    return assistant


def demo():
    """Демо"""
    assistant = create_weather_assistant()

    print("\nПроверьте погоду в Пекине:")
    response = assistant.run("Какая сегодня погода в Пекине?")
    print(f"Ответ: {response}\n")


def interactive():
    """интерактивный режим"""
    assistant = create_weather_assistant()

    while True:
        user_input = input("\nВы: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
        response = assistant.run(user_input)
        print(f"Ассистент: {response}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        interactive()

