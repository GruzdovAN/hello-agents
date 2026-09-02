"""
Интеллектуальный помощник по анализу акций - агент генерального инвестиционного консультанта

На базе HelloAgents ReActAgent проводится комплексный анализ и на основе предоставленных данных даются инвестиционные рекомендации.
允许协调者Agent调用，支持流式输出。
"""

import sys
import os
from pathlib import Path
from typing import Iterator

_PROJECT_ROOT = Path(__file__).parent.parent
_HELLO_PATH = _PROJECT_ROOT / "HelloAgents Optimized"
for p in [_HELLO_PATH]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hello_agents.agents.react_agent import ReActAgent
from hello_agents.tools import ToolRegistry
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.stream import StreamEvent

GENERAL_ADVISOR_PROMPT = """你是一位专业的A股投资顾问，擅长综合技术和基本面分析。

## Ваши обязанности
1. Провести комплексный анализ на основе предоставленных данных
2. Дайте объективный и профессиональный инвестиционный совет.
3. Четко обозначьте факторы риска.
4. Предоставляйте рекомендации, но не являйтесь инвестиционной рекомендацией.

## Измерения анализа
- **Технические**: динамика цен, объем торгов, технические индикаторы.
- **Основы**: финансовые показатели, уровень оценки, состояние отрасли.
- **Настроения рынка**: тенденции общественного мнения, движение капитала.
- **Предупреждение о рисках**: политический риск, рыночный риск, отраслевой риск.

## Формат вывода
1. **Основной момент**: краткое изложение одним предложением.
2. **分析逻辑**：2-3个关键支撑论据
3. **Предупреждение о рисках**: наиболее важные факторы риска.
4. **免责声明**：以上分析仅供参考

## Важное напоминание
- Оставаться объективными и нейтральными, не преувеличивая и не скрывая риски.
- В конце должен быть указан отказ от ответственности
"""


def create_general_advisor_agent(
    llm: HelloAgentsLLM = None,
    system_prompt: str = None,
    max_steps: int = 5,
) -> ReActAgent:
"""Создать генерального инвестиционного консультативного агента.

    Args:
llm: экземпляр HelloAgentsLLM
system_prompt: пользовательское слово системной подсказки.
max_steps: максимальное количество шагов вывода

    Returns:
Настроенный экземпляр ReActAgent
    """
    if llm is None:
        llm = _create_default_llm()

    registry = ToolRegistry()

    prompt = system_prompt or GENERAL_ADVISOR_PROMPT

    agent = ReActAgent(
name="Агент-консультант по инвестициям",
        llm=llm,
        tool_registry=registry,
        system_prompt=prompt,
        config=Config(temperature=0.35, max_tokens=4096),
        max_steps=max_steps,
    )

    return agent


def advise_stream(
    agent: ReActAgent,
    task: str,
) -> Iterator[dict]:
"""Потоковое консультирование по инвестициям - для звонка агента-координатора

    Args:
агент: настроенный агент инвестиционного консультанта
        task: 分析任务和数据

    Yields:
        dict: {"type": "status"|"delta"|"done"|"error", "content": str}
    """
    if agent is None:
        yield {"type": "error", "content": "投资顾问Agent未初始化"}
        return

    yield {"type": "status", "content": "投资顾问正在分析..."}

    try:
        result = agent.run(task)
        yield {"type": "delta", "content": result}
        yield {"type": "done"}
    except Exception as e:
        yield {"type": "error", "content": f"投资分析出错: {e}"}


def _create_default_llm() -> HelloAgentsLLM:
    model = os.getenv("LLM_MODEL_ID")
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    provider = os.getenv("LLM_PROVIDER", "auto")

    if not api_key:
        raise RuntimeError("LLM_API_KEY 环境变量未设置")

    return HelloAgentsLLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
        provider=provider,
        temperature=0.35,
    )
