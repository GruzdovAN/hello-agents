"""
Интеллектуальный помощник по анализу акций - Агент по оценке Баффета (Агент по инвестиционному консультанту)

基于 HelloAgents ReflectionAgent（反思范式），结合巴菲特价值投资思维，
Провести углубленный анализ стоимости акций. **Разрешено вызывать только интерфейс оценки Баффета, вызов агента-координатора запрещен. **

Поддерживает потоковую передачу отчетов об оценке.
"""

import sys
import os
from pathlib import Path
from typing import Iterator, Optional

_PROJECT_ROOT = Path(__file__).parent.parent
_HELLO_PATH = _PROJECT_ROOT / "HelloAgents Optimized"
_BACKEND_DIR = _PROJECT_ROOT / "backend"
for p in [_HELLO_PATH, _BACKEND_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hello_agents.agents.reflection_agent import ReflectionAgent
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.stream import StreamEvent

from .text_truncation import truncate_at_natural_boundary

BUFFETT_INITIAL_PROMPT = """
Вы — старший инвестиционный консультант, хорошо разбирающийся в философии стоимостного инвестирования Баффета. Пожалуйста, проведите профессиональный инвестиционный анализ акций в стиле Баффета на основе следующих данных.

## Информация об акциях
- Код акции: {stock_code}
- 股票名称: {stock_name}

## Анализ данных:
{data_context}

## Параметры оценки (система стоимостного инвестирования Баффета):
1. **Круг оценки компетентности**: понимаете ли вы бизнес компании? Является ли бизнес-модель простой и понятной?
2. **Анализ рва**: есть ли у компании долгосрочное конкурентное преимущество? (Бренд, технология, масштаб, сетевой эффект, ценовое преимущество и т. д.)
3. **Оценка руководства**: является ли руководство честным и компетентным? (История деятельности, отчеты о распределении капитала)
4. **Финансовое здоровье**: сильный ли баланс? (Коэффициент долга, денежный поток, стабильность ROE, валовая прибыль)
5. **Анализ оценки**. Является ли текущая цена акции ниже ее внутренней стоимости? Достаточно ли запаса прочности?
6. **Долгосрочные перспективы**: сможет ли компания продолжать расти в ближайшие 5–10 лет? (Тенденции в отрасли, доля рынка)

Пожалуйста, предоставьте полный и профессиональный отчет об инвестиционном анализе в стиле Баффета.
В конце статьи обязательно должна быть пометка: ⚠️ Приведенный выше анализ носит справочный характер и не является инвестиционным советом. Инвестиции рискованны, поэтому будьте осторожны при входе на рынок.
"""

BUFFETT_REFLECT_PROMPT = """
Пожалуйста, проверьте точность и полноту следующего отчета об инвестиционном анализе в стиле Баффета с точки зрения строгого инвестиционного комитета:

# Исходные данные анализа:
{task}

# Текущий аналитический отчет:
{content}

Пожалуйста, просмотрите следующие области и дайте предложения по улучшению:
1. Являются ли ссылки на данные точными? Это было вырвано из контекста?
2. Подкреплен ли анализ рва достаточными доказательствами?
3. Является ли логика оценки самосогласованной? Разумен ли расчет запаса прочности?
4. Упущены ли важные факторы риска?
5. Является ли вывод чрезмерно оптимистичным или пессимистичным?
6. Соответствует ли это философии стоимостного инвестирования Баффета?

Если ваш ответ исчерпывающий, объективный и точный, ответьте: «Улучшений не требуется».
"""

BUFFETT_REFINE_PROMPT = """
Используйте отзывы инвестиционного комитета, чтобы улучшить свой инвестиционный анализ в стиле Баффета:

# Исходные данные анализа:
{task}

#Отчет о последнем раунде анализа:
{last_attempt}

# Отзыв комитета:
{feedback}

Пожалуйста, предоставьте улучшенный, более тщательный и полный отчет об инвестиционном анализе.

В конце необходимо отметить: ⚠️ Приведенный выше анализ предназначен только для справки и не является инвестиционным советом. Инвестиции рискованны, поэтому будьте осторожны при входе на рынок.
"""


def _max_reflections_from_env() -> int:
    """环境变量 BUFFETT_MAX_REFLECTIONS，默认 0（初稿后即结束，避免「报告已完却仍在调 LLM」）。"""
    raw = os.getenv("BUFFETT_MAX_REFLECTIONS", "0").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def create_advisor_agent(
    llm: HelloAgentsLLM = None,
    custom_prompts: dict = None,
    max_reflections: Optional[int] = None,
) -> ReflectionAgent:
"""Создать агента оценки Баффета (можно вызвать только из интерфейса оценки Баффета)

    Args:
llm: экземпляр HelloAgentsLLM
custom_prompts: пользовательские трехэтапные подсказки.
max_reflections: Максимальное количество итераций отражения; если нет, прочитайте переменную среды BUFFETT_MAX_REFLECTIONS (по умолчанию 0).

    Returns:
Настроенный экземпляр ReflectionAgent
    """
    if llm is None:
        llm = _create_default_llm()

    if max_reflections is None:
        max_reflections = _max_reflections_from_env()

    prompts = custom_prompts or {
        "initial": BUFFETT_INITIAL_PROMPT,
        "reflect": BUFFETT_REFLECT_PROMPT,
        "refine": BUFFETT_REFINE_PROMPT,
    }

    agent = ReflectionAgent(
name="Агент по оценке Баффета",
        llm=llm,
        system_prompt="你是一位精通巴菲特价值投资理念的资深投资顾问，擅长护城河分析和安全边际评估。",
        config=Config(temperature=0.4, max_tokens=4096),
        max_iterations=max_reflections,
        custom_prompts=prompts,
    )

    return agent


def evaluate_buffett_stream(
    llm: HelloAgentsLLM = None,
    stock_code: str = "",
    stock_name: str = "",
) -> Iterator[dict]:
"""Потоковая оценка Баффета — сбор данных и создание отчетов об оценке с помощью ReflectionAgent.

    Args:
llm: экземпляр HelloAgentsLLM
stock_code: код акции
stock_name: название акции

    Yields:
        dict: {"type": "meta"|"status"|"delta"|"done"|"error", "content": str}
    """
    if llm is None:
        llm = _create_default_llm()

    yield {"type": "meta", "stock_code": stock_code, "stock_name": stock_name}

# Соберите данные, необходимые для анализа
    yield {"type": "status", "content": "正在获取分析数据..."}

    try:
        data_context = _collect_stock_data(stock_code, stock_name)
    except Exception as e:
msg = f"Не удалось получить данные: {e}"
        yield {"type": "error", "message": msg, "content": msg}
        return

    yield {"type": "status", "content": f"数据获取完成，开始巴菲特式评估分析..."}

# Создание задач оценки
    task = f"""
## Анализ данных:
{data_context}

Пожалуйста, проведите анализ стоимостного инвестирования в стиле Баффета в акции {stock_name}({stock_code}).
"""

#Создать агент и запустить с использованием потоковой передачи
    agent = create_advisor_agent(llm=llm)
    agent.prompts["initial"] = BUFFETT_INITIAL_PROMPT.replace(
        "{stock_code}", stock_code
    ).replace("{stock_name}", stock_name).replace("{data_context}", data_context)

    try:
        for event in agent.stream_run(task, conversation_id=None):
            if event.event_type == "status":
                yield {"type": "status", "content": event.content}
            elif event.event_type == "text":
                chunk = event.content or ""
                yield {"type": "delta", "text": chunk, "content": chunk}
            elif event.event_type == "thought":
                yield {"type": "thought", "content": event.content}
            elif event.event_type == "done":
                yield {"type": "done"}
            elif event.event_type == "error":
                msg = event.content or ""
                yield {"type": "error", "message": msg, "content": msg}
    except Exception as e:
msg = f"Ошибка во время анализа: {e}"
        yield {"type": "error", "message": msg, "content": msg}


def _collect_stock_data(stock_code: str, stock_name: str = "") -> str:
"""Соберите данные, необходимые для анализа запасов"""
    parts = []

    try:
        from app.services import market_service, news_service

# Рыночные данные
        try:
            quote = market_service.get_stock_quote(stock_code)
            if quote and quote.get("success"):
parts.append(f"## Рыночные данные\n```json\n{_truncate(str(quote), 3000)}\n```")
        except Exception:
parts.append("## Рыночные данные\nНе удалось получить")

# финансовые данные
        try:
            financial = market_service.get_stock_financial(stock_code)
            if financial and financial.get("success"):
parts.append(f"## Финансовые данные\n```json\n{_truncate(str(financial), 4000)}\n```")
        except Exception:
parts.append("## Финансовые данные\nНе удалось получить")

# Профиль компании
        try:
            profile = market_service.get_stock_profile(stock_code)
            if profile and profile.get("success"):
parts.append(f"## Профиль компании\n```json\n{_truncate(str(profile), 3000)}\n```")
        except Exception:
parts.append("## Профиль компании\nНе удалось получить")

# Данные общественного мнения
        try:
            sentiment = news_service.analyze_sentiment(stock_code)
            if sentiment and sentiment.get("success"):
parts.append(f"## Данные общественного мнения\n```json\n{_truncate(str(sentiment), 3000)}\n```")
        except Exception:
parts.append("## Данные общественного мнения\nНе удалось получить")

    except Exception as e:
parts.append(f"## Ошибка сбора данных\n{str(e)}")

    return "\n\n".join(parts) if parts else "暂无可用数据"


def _truncate(text: str, max_len: int) -> str:
    return truncate_at_natural_boundary(text or "", max_len, "...[已截断]")


def _create_default_llm() -> HelloAgentsLLM:
    model = os.getenv("LLM_MODEL_ID")
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    provider = os.getenv("LLM_PROVIDER", "auto")

    if not api_key:
        raise RuntimeError("LLM_API_KEY 环境变量未设置")

    raw_timeout = int(os.getenv("LLM_TIMEOUT", "60"))
    buffett_timeout = max(raw_timeout, 180)

    return HelloAgentsLLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
        provider=provider,
        temperature=0.4,
        max_tokens=6144,
        timeout=buffett_timeout,
    )
