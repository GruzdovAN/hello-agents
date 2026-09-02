"""
Интеллектуальный помощник по анализу акций — агент анализа данных

基于 HelloAgents ReActAgent，使用 mx_data 工具查询行情和财务数据，
Проведите углубленный фундаментальный и технический анализ.

Как использовать:
    from agents.data_analysis_agent import create_data_analysis_agent

    agent = create_data_analysis_agent(api_key="...", llm=llm)
result = Agent.run("Анализ финансовых показателей и уровней оценки Kweichow Moutai")
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
_HELLO_PATH = _PROJECT_ROOT / "HelloAgents Optimized"
_AGENTS_DIR = _PROJECT_ROOT / "agents"
_BACKEND_DIR = _PROJECT_ROOT / "backend"
_SKILLS_DATA = _PROJECT_ROOT / "skills" / "金融数据" / "mx-data"

for p in [_HELLO_PATH, _AGENTS_DIR, _BACKEND_DIR, _SKILLS_DATA]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from typing import Iterator

from hello_agents.tools import ToolRegistry
from hello_agents.agents.react_agent import ReActAgent
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.stream import StreamEvent

from agents.tools.mx_data_tool import MXDataTool

# Слово подсказки системы агента анализа данных
DATA_ANALYSIS_PROMPT = """你是一位专业的A股数据分析师，精通基本面分析和技术面分析。

## Ваши обязанности
1. Запросите в режиме реального времени рыночные данные о целевой акции (цена, увеличение или уменьшение, объем торгов, скорость оборота и т. д.).
2. Анализ основных финансовых показателей (ROE, чистая прибыль, темпы роста выручки, валовая прибыль и т. д.)
3. Оцените уровни оценки (отношение цены к прибыли, соотношение цены к балансовой стоимости, дивидендная доходность и т. д.)
4. Просмотрите основной профиль компании (основной бизнес, статус отрасли, высшее руководство и т. д.).
5. В сочетании с многомерными данными для обеспечения комплексной оценки фундаментальных и технических аспектов.

## Структура анализа
- **Рентабельность**: рентабельность собственного капитала, чистая прибыль, валовая прибыль, темпы роста выручки.
- **Уровень оценки**: PE, PB, PS, PEG
– **Рост**: совокупный темп роста выручки/прибыли за последние три года.
- **Денежный поток**: соотношение операционного денежного потока к чистой прибыли.
- **Дивиденды**: ставка дивидендов, ставка дивидендов, стабильность дивидендов.

## Формат вывода
Результаты анализа должны включать:
1. **Снимок рынка**: последняя цена, увеличение и уменьшение, статус транзакции.
2. **Финансовое здоровье**: Радарная диаграмма оценки основных показателей
3. **Квантиль оценки**: положение текущей оценки в историческом диапазоне.
4. **Особенности и риски**: 2–3 ключевых вывода.

## Важное напоминание
- Прежде всего данные, все выводы должны быть подтверждены данными запроса.
- Отметьте временной интервал при сравнении истории
- Отказ от ответственности в конце

## ReAct 回合输出（与框架对接，必须遵守）
每一轮模型回复都必须同时包含下面两行（缺一不可），禁止只输出 Markdown 报告正文而不写 Action：
- `Мысль:` Одна строка краткого рассуждения (можно выбрать одно из китайских слов «Мысль:», но рекомендуется использовать английские теги)
- `Action:` 要么是 `mx_data[查询指令]`，要么是 **最终结论** `Finish[完整分析报告正文]`

При подготовке к выводу окончательного отчета вы также должны использовать `Action: Finish[...]` для переноса полного текста; `[` и окончание `]` должны быть парными. Если в отчете необходимы скобки, избегайте использования отдельного `]`, чтобы разрушить пару, или сжимайте длинный отчет в оператор, не содержащий голого `]`.
"""


def create_data_analysis_agent(
    api_key: str = None,
    llm: HelloAgentsLLM = None,
    system_prompt: str = None,
    max_steps: int = 8,
) -> ReActAgent:
"""Создать агент анализа данных

    Args:
api_key: Восточная удача MX_APIKEY
llm: экземпляр HelloAgentsLLM (обязательно)
system_prompt: пользовательское слово системной подсказки (необязательно).
max_steps: максимальное количество шагов вывода, по умолчанию 8 (для анализа данных требуется многоэтапный запрос)

    Returns:
Настроенный экземпляр ReActAgent
    """
    if llm is None:
        llm = _create_default_llm()

    registry = ToolRegistry()
    data_tool = MXDataTool(api_key=api_key)
    registry.register_tool(data_tool)

    prompt = system_prompt or DATA_ANALYSIS_PROMPT

    agent = ReActAgent(
name="Агент анализа данных",
        llm=llm,
        tool_registry=registry,
        system_prompt=prompt,
        config=Config(temperature=0.2, max_tokens=4096),
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
        temperature=0.2,
    )


def analyze_data_stream(
    agent: ReActAgent,
    stock_code: str = "",
    stock_name: str = "",
) -> Iterator[dict]:
"""Потоковый анализ данных — запрос и анализ рыночных и финансовых данных с помощью ReActAgent.

    Args:
агент: настроенный агент анализа данных
stock_code: код акции
stock_name: название акции

    Yields:
        dict: {"type": "meta"|"status"|"delta"|"done"|"error", "content": str}
    """
    stock_label = f"{stock_name}({stock_code})" if stock_name else stock_code

    yield {"type": "meta", "stock_code": stock_code, "stock_name": stock_name}
доходность {"type": "status", "content": f"Запрос рыночных и финансовых данных {stock_label}..."}

    task = f"""请查询股票 {stock_label} 的以下数据并进行综合分析：
1. Рыночные условия в режиме реального времени (цена, увеличение или уменьшение, объем торгов, скорость оборота и т. д.)
2. Основные финансовые показатели (ROE, чистая прибыль, темпы роста выручки, валовая прибыль и т. д.)
3. Уровень оценки (отношение цены к прибыли, соотношение цены к балансовой стоимости, дивидендная доходность и т. д.)
4. Базовый обзор компании

Пожалуйста, предоставьте профессиональный отчет по анализу данных. """

    try:
        for event in agent.stream_run(task):
            if event.event_type == "status":
                yield {"type": "status", "content": event.content}
            elif event.event_type in ("text", "observation"):
                yield {"type": "delta", "content": event.content}
            elif event.event_type == "tool_call":
доходность {"тип": "статус", "контент": f"Запрос: {event.metadata.get('tool_name', '')}"}
            elif event.event_type == "done":
                yield {"type": "done"}
            elif event.event_type == "error":
                yield {"type": "error", "content": event.content}
    except Exception as e:
        yield {"type": "error", "content": f"数据分析出错: {e}"}
