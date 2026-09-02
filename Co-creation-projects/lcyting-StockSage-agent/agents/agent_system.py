"""
Интеллектуальный помощник по анализу запасов — агентская система (унифицированное управление агентами и планирование потоковой передачи)

На основе оптимизированной платформы HelloAgents управляйте жизненным циклом всех профессиональных агентов,
Предоставляет унифицированный интерфейс анализа потоковой передачи для вызовов API серверной части.
"""

import sys
import os
import threading
from pathlib import Path
from typing import AsyncIterator, Optional


def _coord_answer_cap_hint(max_chars: int) -> str:
    return (
        f"\n\n【硬性要求】最终答案全文不得超过约 {max_chars} 个汉字（含标点），"
«Будьте лаконичны и лаконичны. Запрещено вставлять полный текст или большие разделы, возвращаемые инструментом перефразирования».
    )


def _apply_answer_cap(text: str, max_chars: Optional[int]) -> str:
    if max_chars is None or max_chars <= 0:
        return text or ""
    from .text_truncation import truncate_at_natural_boundary

    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
return truncate_at_natural_boundary(t, max_chars, "\n\n…(достигнуто максимальное количество символов)")

_HELLO_AGENTS_PATH = Path(__file__).parent.parent / "HelloAgents Optimized"
if str(_HELLO_AGENTS_PATH) not in sys.path:
    sys.path.insert(0, str(_HELLO_AGENTS_PATH))

_SKILLS_PATH = Path(__file__).parent.parent / "skills"
if str(_SKILLS_PATH) not in sys.path:
    sys.path.insert(0, str(_SKILLS_PATH))

_BACKEND_PATH = Path(__file__).parent.parent / "backend"
if str(_BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(_BACKEND_PATH))

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config

_agent_lock = threading.Lock()
_agent_system_instance: Optional["AgentSystem"] = None


class AgentSystem:
"""Агентная система — унифицированно управляет всеми агентами и предоставляет интерфейс потокового анализа"""

    def __init__(self):
        self._llm: Optional[HelloAgentsLLM] = None
        self._advisor = None         # 巴菲特评估 Agent (Reflection)
        self._sentiment = None       # 舆情分析 Agent (ReAct)
        self._data_analysis = None   # 数据分析 Agent (ReAct)
        self._general_advisor = None # 普通投资顾问 Agent
        self._initialized = False

    def _ensure_llm(self) -> HelloAgentsLLM:
        if self._llm is None:
            self._llm = _create_default_llm()
        return self._llm

    def _get_api_key(self) -> Optional[str]:
        key = os.getenv("MX_APIKEY", "").strip()
        if key and key != "your-mx-apikey-here":
            return key
        try:
            from app.config import settings
            return settings.MX_APIKEY or None
        except Exception:
            return None

# ---- Баффет оценивает агента ----

    def get_advisor_agent(self):
"""Получить агента оценки Баффета (можно вызвать только из интерфейса оценки Баффета)"""
        if self._advisor is None:
            from agents.advisor_agent import create_advisor_agent
            self._advisor = create_advisor_agent(llm=self._ensure_llm())
        return self._advisor

    def evaluate_buffett_stream(self, stock_code: str, stock_name: str = ""):
"""Потоковая оценка Баффета — создание отчета об оценке через Advisor_agent"""
        from agents.advisor_agent import evaluate_buffett_stream
        yield from evaluate_buffett_stream(
            llm=self._ensure_llm(),
            stock_code=stock_code,
            stock_name=stock_name,
        )

# ---- Агент анализа общественного мнения ----

    def get_sentiment_agent(self):
"""Получить агент по анализу общественного мнения"""
        if self._sentiment is None:
            from agents.sentiment_agent import create_sentiment_agent
            self._sentiment = create_sentiment_agent(
                api_key=self._get_api_key(),
                llm=self._ensure_llm(),
            )
        return self._sentiment

    def run_sentiment(
        self,
        stock_code: str,
        stock_name: str = "",
        *,
        max_answer_chars: Optional[int] = None,
    ) -> str:
"""Непотоковый анализ общественного мнения — возвращает полный текст для внутренних звонков Агента-координатора"""
        agent = self.get_sentiment_agent()
        stock_label = f"{stock_name}({stock_code})" if stock_name else stock_code
        task = f"请搜索并分析股票 {stock_label} 的最新金融资讯、研究报告和公告，判断市场舆情趋势。"
        if max_answer_chars:
            task += _coord_answer_cap_hint(max_answer_chars)
        try:
            out = (agent.run(task) or "").strip()
            if not out:
                return (
                    "[舆情分析未生成有效正文：可能因网络/超时或模型提前结束。"
«Рекомендуется использовать потоковую передачу «Анализ общественного мнения AI» на отдельных страницах акций, чтобы повторить попытку, или сбросить серверную часть после настройки LLM_TIMEOUT на 300 в .env.]»
                )
            return _apply_answer_cap(out, max_answer_chars)
        except Exception as e:
return f"[Анализ общественного мнения не удался: {e}]"

    def analyze_sentiment_stream(self, stock_code: str, stock_name: str = ""):
"""Потоковое анализ общественного мнения"""
        from agents.sentiment_agent import analyze_sentiment_stream
        yield from analyze_sentiment_stream(
            agent=self.get_sentiment_agent(),
            stock_code=stock_code,
            stock_name=stock_name,
        )

# ---- Агент анализа данных ----

    def get_data_analysis_agent(self):
"""Получить агент анализа данных"""
        if self._data_analysis is None:
            from agents.data_analysis_agent import create_data_analysis_agent
            self._data_analysis = create_data_analysis_agent(
                api_key=self._get_api_key(),
                llm=self._ensure_llm(),
            )
        return self._data_analysis

    def run_data_analysis(
        self,
        stock_code: str,
        stock_name: str = "",
        *,
        max_answer_chars: Optional[int] = None,
    ) -> str:
"""Непотоковый анализ данных — возвращает полный текст внутренних звонков Агента-координатора"""
        agent = self.get_data_analysis_agent()
        stock_label = f"{stock_name}({stock_code})" if stock_name else stock_code
        task = f"""请查询股票 {stock_label} 的以下数据并进行综合分析：
1. Рыночные условия в режиме реального времени (цена, увеличение или уменьшение, объем торгов, скорость оборота и т. д.)
2. Основные финансовые показатели (ROE, чистая прибыль, темпы роста выручки, валовая прибыль и т. д.)
3. Уровень оценки (отношение цены к прибыли, соотношение цены к балансовой стоимости, дивидендная доходность и т. д.)
4. Базовый обзор компании

Пожалуйста, предоставьте профессиональный отчет по анализу данных. """
        if max_answer_chars:
            task += _coord_answer_cap_hint(max_answer_chars)
        try:
            out = (agent.run(task) or "").strip()
            if not out:
                return (
                    "[数据分析未生成有效正文：可能因网络/超时或模型提前结束。"
«Рекомендуется использовать потоковую передачу «Анализ данных AI» на отдельной странице или настроить LLM_TIMEOUT на 300 в .env, а затем перезапустить серверную часть.]»
                )
            return _apply_answer_cap(out, max_answer_chars)
        except Exception as e:
return f"[Ошибка анализа данных: {e}]"

    def analyze_data_stream(self, stock_code: str, stock_name: str = ""):
"""Потоковый анализ данных"""
        from agents.data_analysis_agent import analyze_data_stream
        yield from analyze_data_stream(
            agent=self.get_data_analysis_agent(),
            stock_code=stock_code,
            stock_name=stock_name,
        )

# ---- Обычный инвестиционный консультант-агент ----

    def get_general_advisor_agent(self):
"""Найдите генерального инвестиционного консультанта"""
        if self._general_advisor is None:
            from agents.general_advisor_agent import create_general_advisor_agent
            self._general_advisor = create_general_advisor_agent(
                llm=self._ensure_llm(),
            )
        return self._general_advisor

    def run_advisor(
        self,
        task: str,
        *,
        max_answer_chars: Optional[int] = None,
    ) -> str:
"""Непотоковая инвестиционная консультация — возвращает полный текст для внутренних звонков агента-координатора"""
        agent = self.get_general_advisor_agent()
        if max_answer_chars:
            task = task + _coord_answer_cap_hint(max_answer_chars)
        try:
            out = (agent.run(task) or "").strip()
            return _apply_answer_cap(out, max_answer_chars)
        except Exception as e:
return f"[Инвестиционный анализ не удался: {e}]"

# ---- AI-помощник по диалогу (координатор) ----

    def chat_stream(self, user_message: str, history: list = None):
"""Интерфейс потоковой передачи AI Dialogue Assistant — агент-координатор анализирует потребности пользователей и планирует работу субагентов"""
        from agents.coordinator_agent import coordinator_chat_stream
        yield from coordinator_chat_stream(
            llm=self._ensure_llm(),
            user_message=user_message,
            history=history or [],
            agent_system=self,
        )

# ---- Проверка работоспособности ----

    def is_ready(self) -> bool:
        try:
            self._ensure_llm()
            return True
        except Exception:
            return False


def _create_default_llm() -> HelloAgentsLLM:
    model = os.getenv("LLM_MODEL_ID")
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    provider = os.getenv("LLM_PROVIDER", "auto")

    if not api_key:
        raise RuntimeError("LLM_API_KEY 环境变量未设置")

    try:
        from app.config import settings

        raw_timeout = int(settings.LLM_TIMEOUT)
    except Exception:
        raw_timeout = int(os.getenv("LLM_TIMEOUT", "60"))
# Многораундовая серия ReAct + вызов инструмента + серия координаторов с несколькими агентами, значение по умолчанию — 60 с, и время ожидания легко прерваться на полпути.
    timeout = max(raw_timeout, 180)

    return HelloAgentsLLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
        provider=provider,
        temperature=0.3,
        max_tokens=8192,
        timeout=timeout,
    )


def get_agent_system() -> AgentSystem:
"""Получить глобальный синглтон AgentSystem"""
    global _agent_system_instance
    if _agent_system_instance is None:
        with _agent_lock:
            if _agent_system_instance is None:
                _agent_system_instance = AgentSystem()
    return _agent_system_instance
