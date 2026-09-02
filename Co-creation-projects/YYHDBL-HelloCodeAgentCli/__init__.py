"""
HelloAgents — гибкий, расширяемый мультиагентный фреймворк

Построен на нативном API OpenAI и даёт простой и эффективный опыт разработки агентов (Agent).
"""

# Уровни логирования сторонних библиотек — меньше шума
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("qdrant_client").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("neo4j.notifications").setLevel(logging.WARNING)

from .version import __version__, __author__, __email__, __description__

# Компоненты ядра
from .core.llm import HelloAgentsLLM
from .core.config import Config
from .core.message import Message
from .core.exceptions import HelloAgentsException

# Реализации Agent
from .agents.simple_agent import SimpleAgent
from .agents.react_agent import ReActAgent
from .agents.reflection_agent import ReflectionAgent
from .agents.plan_solve_agent import PlanAndSolveAgent

# Система инструментов
from .tools.registry import ToolRegistry, global_registry
from .tools.builtin.search import SearchTool, search
from .tools.builtin.calculator import CalculatorTool, calculate
from .tools.chain import ToolChain, ToolChainManager
from .tools.async_executor import AsyncToolExecutor

__all__ = [
    # Информация о версии
    "__version__",
    "__author__",
    "__email__",
    "__description__",

    # Компоненты ядра
    "HelloAgentsLLM",
    "Config",
    "Message",
    "HelloAgentsException",

    # Парадигмы Agent
    "SimpleAgent",
    "ReActAgent", 
    "ReflectionAgent",
    "PlanAndSolveAgent",

    # Система инструментов
    "ToolRegistry",
    "global_registry",
    "SearchTool",
    "search",
    "CalculatorTool",
    "calculate",
    "ToolChain",
    "ToolChainManager",
    "AsyncToolExecutor",
]

