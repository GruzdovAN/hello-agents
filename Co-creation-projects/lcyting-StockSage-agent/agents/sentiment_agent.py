"""
Интеллектуальный помощник по анализу акций — агент по анализу общественного мнения

На основе HelloAgents ReActAgent используйте инструмент mx-search для поиска финансовой информации.
И объединитесь с LLM для проведения анализа эмоциональных тенденций, а также исследований и суждений общественного мнения.

Как использовать:
    from agents.sentiment_agent import create_sentiment_agent

    agent = create_sentiment_agent(api_key="...", llm=llm)
result = Agent.run("Анализ ситуации с общественным мнением о Квейчоу Моутае")
"""

import sys
from pathlib import Path

#Добавляем путь к фреймворку в sys.path
_PROJECT_ROOT = Path(__file__).parent.parent
_HELLO_PATH = _PROJECT_ROOT / "HelloAgents Optimized"
_AGENTS_DIR = _PROJECT_ROOT / "agents"
_BACKEND_DIR = _PROJECT_ROOT / "backend"
_SKILLS_SEARCH = _PROJECT_ROOT / "skills" / "资讯搜索" / "mx-search"

for p in [_HELLO_PATH, _AGENTS_DIR, _BACKEND_DIR, _SKILLS_SEARCH]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from typing import Iterator

from hello_agents.tools import ToolRegistry
from hello_agents.agents.react_agent import ReActAgent
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.stream import StreamEvent

from agents.tools.mx_search_tool import MXSearchTool

#Подсказки системы анализа общественного мнения по умолчанию
SENTIMENT_SYSTEM_PROMPT = """你是一位专业的金融舆情分析师，精通A股市场和各种政策分析方法论。

## Ваши обязанности
1. Поиск последней финансовой информации (новостей, исследовательских отчетов, объявлений) по целевой акции/отрасли.
2. Проанализируйте эмоциональную направленность каждой части информации (положительная/отрицательная/нейтральная).
3. Определить критические события и потенциальные последствия.
4. Всесторонне оценить тенденции рыночного общественного мнения.
5. Предоставить объективные и подтвержденные данными исследования общественного мнения и выводы.

## Метод анализа
- Обратите внимание на авторитетность источников информации (официальные объявления > авторитетные исследовательские отчеты > новостные сообщения).
- Обращайте внимание на своевременность информации (чем новее, тем важнее)
- Различайте краткосрочные колебания настроения и долгосрочные изменения тенденций.
- Обратите внимание на выявление потенциальных хороших/плохих событий.
- Анализировать на основе отраслевой политики.

## Формат вывода
Результаты анализа должны содержать следующие разделы:
1. **Обзор общественного мнения**: статистика эмоционального распределения (положительные X пунктов/отрицательные X пунктов/нейтральные X пунктов)
2. **Основное событие**: 2–3 наиболее важных сводки ключевой информации.
3. **Эмоциональный тренд**: общая предвзятость общественного мнения и меняющиеся тенденции.
4. **Предупреждение о рисках**: потенциальные риски и неопределенности, требующие внимания.
5. **Комплексное исследование и суждение**: Рекомендации по инвестициям, основанные на анализе общественного мнения (не являются инвестиционными рекомендациями).

## Важное напоминание
- Всегда оставайтесь объективными и нейтральными, не преувеличивая и не скрывая риски.
- Все выводы анализа должны быть подтверждены результатами поиска.
- В конце должна быть пометка «Приведенный выше анализ предназначен только для справки и не является инвестиционной рекомендацией».
"""


def create_sentiment_agent(
    api_key: str = None,
    llm: HelloAgentsLLM = None,
    system_prompt: str = None,
    max_steps: int = 8,
) -> ReActAgent:
"""Создать агента по анализу общественного мнения

    Args:
api_key: Oriental Fortune MX_APIKY, если не указан, он будет прочитан из переменной среды.
llm: экземпляр HelloAgentsLLM (обязательно), автоматически создается из переменных среды, если они не указаны.
system_prompt: пользовательское слово системной подсказки (необязательно).
max_steps: максимальное количество шагов вывода, по умолчанию 8 (поиск + синтез часто требует нескольких шагов)

    Returns:
Настроенный экземпляр ReActAgent

    Raises:
RuntimeError: если LLM не настроен и не может быть создан из переменных среды.
    """
# Создать экземпляр LLM (если не указано)
    if llm is None:
        llm = _create_default_llm()

    # 创建工具注册表并注册资讯搜索工具
    registry = ToolRegistry()
    search_tool = MXSearchTool(api_key=api_key)
    registry.register_tool(search_tool)

# Используйте пользовательские или системные слова подсказки по умолчанию
    prompt = system_prompt or SENTIMENT_SYSTEM_PROMPT

# Создать ReActAgent
    agent = ReActAgent(
name="Агент по анализу общественного мнения",
        llm=llm,
        tool_registry=registry,
        system_prompt=prompt,
        config=Config(temperature=0.3, max_tokens=4096),  # 低温度确保分析稳定
        max_steps=max_steps,
    )

    return agent


def _create_default_llm() -> HelloAgentsLLM:
"""Создать экземпляр LLM по умолчанию из переменных среды"""
    import os

    model = os.getenv("LLM_MODEL_ID")
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    provider = os.getenv("LLM_PROVIDER", "auto")

    if not api_key:
        raise RuntimeError(
«Переменная среды LLM_API_KEY не установлена, сначала установите переменную среды:\n»
            "export LLM_API_KEY=your_llm_api_key_here\n"
«Или передайте параметр llm при создании агента»
        )

    return HelloAgentsLLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
        provider=provider,
        temperature=0.3,
    )


def analyze_sentiment_stream(
    agent: ReActAgent,
    stock_code: str = "",
    stock_name: str = "",
) -> Iterator[dict]:
"""Потоковый анализ общественного мнения - поиск информации и анализ общественного мнения через ReActAgent

    Args:
агент: Настроенный анализ общественного мнения Агент
stock_code: код акции
stock_name: название акции

    Yields:
        dict: {"type": "meta"|"status"|"delta"|"done"|"error", "content": str}
    """
    stock_label = f"{stock_name}({stock_code})" if stock_name else stock_code

    yield {"type": "meta", "stock_code": stock_code, "stock_name": stock_name}
доходность {"type": "status", "content": f"Поиск информации, связанной с {stock_label}..."}

    task = f"请搜索并分析股票 {stock_label} 的最新金融资讯、研究报告和公告，判断市场舆情趋势。"

    try:
        for event in agent.stream_run(task):
            if event.event_type == "status":
                yield {"type": "status", "content": event.content}
            elif event.event_type in ("text", "observation"):
                yield {"type": "delta", "content": event.content}
            elif event.event_type == "tool_call":
выход {"тип": "статус", "контент": f"Вызов инструмента: {event.metadata.get('tool_name', '')}"}
            elif event.event_type == "done":
                yield {"type": "done"}
            elif event.event_type == "error":
                yield {"type": "error", "content": event.content}
    except Exception as e:
        yield {"type": "error", "content": f"舆情分析出错: {e}"}
