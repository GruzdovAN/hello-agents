# src/agents/mind_echo_agent.py

from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool, A2ATool
from src.tools.dialogue_state_tool import DialogueStateTool
from src.tools.mood_music_tool import MoodMusicTool
from src.tools.text_comfort_tool import TextComfortTool
from src.tools.mood_summary_tool import MoodSummaryTool
from src.utils.state import DialogueState

def create_mind_echo_agent(user_id: str = "user001"):
    llm = HelloAgentsLLM()

    system_prompt = """
Ты MindEchoAgent (Эхо настроения), отвечаешь за эмоциональное сопровождение и музыкальные рекомендации.
Ты должен:
1) Распознавать настроение пользователя; в каждом диалоге сначала определять состояние (MOOD/COMFORT/MUSIC/ESCALATE)
2) По состоянию вызывать нужный инструмент: успокоение / музыкальные рекомендации
3) При ключевых словах «постоянная тревога», «не могу уснуть», «бессонница» или состоянии ESCALATE — эскалировать к SleepAgent (A2A)
"""

    agent = SimpleAgent(
        name="MindEchoAgent",
        llm=llm,
        system_prompt=system_prompt
    )

    registry = ToolRegistry()
    registry.register_tool(MemoryTool(user_id=user_id))
    registry.register_tool(DialogueStateTool())
    registry.register_tool(TextComfortTool())
    registry.register_tool(MoodMusicTool())
    registry.register_tool(MoodSummaryTool())

    # A2A-инструмент: сервис SleepAgent
    sleep_tool = A2ATool(
        agent_url="http://localhost:6000",  # стандартный порт SleepAgent
        name="sleep_agent",
        description="Эксперт по сну: бессонница, тревога и др."
    )
    registry.register_tool(sleep_tool)

    agent.tool_registry = registry
    agent.current_state = DialogueState.INIT.value

    return agent
