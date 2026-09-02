"""Step 5-8: HelloAgents 框架 StockInsightAgent + Memory + RAG + Context
Инструменты: 5 данных + 7 памяти + 3 базы знаний + 3 контекста.
模式: ReActAgent / PlanSolveAgent / ReflectionAgent
"""
from dotenv import load_dotenv
load_dotenv()

from hello_agents import (
    HelloAgentsLLM, ToolRegistry,
    ReActAgent, PlanSolveAgent, ReflectionAgent
)
from tools import (
    get_realtime_quote, get_historical_data,
    get_financial_data, calc_indicators, get_news
)
from memory import (
    memory_add_watchlist, memory_remove_watchlist, memory_get_watchlist,
    memory_save_analysis, memory_get_history,
    memory_set_preference, memory_get_preferences,
)
from rag import rag_search, rag_import, rag_stats
from context_manager import get_context, context_stats, context_clear, context_summarize


def build_tool_registry():
"""Зарегистрируйте все инструменты: 5 данных + 7 ячеек памяти"""
    registry = ToolRegistry()

# инструменты обработки данных
    registry.register_function(get_realtime_quote, "GetRealtimeQuote",
«Получить котировки акций A в реальном времени (последняя цена/увеличение/объем/цена/рыночная стоимость). Введите: код акции или аббревиатуру»)
    registry.register_function(get_historical_data, "GetHistoricalData",
        "获取历史K线数据(OHLCV)。输入格式: '代码|周期|天数'，如'600519|daily|60'")
    registry.register_function(get_financial_data, "GetFinancialData",
        "获取核心财务指标(净利润/营收/毛利率/负债率/ROE等)。输入: 股票代码")
    registry.register_function(calc_indicators, "CalcIndicators",
«Рассчитать технические индикаторы (MA5/10/20/60, MACD, RSI14, полосы Боллинджера, уровень давления поддержки). Формат ввода: 'код|ежедневно|дни'")
    registry.register_function(get_news, "GetNews",
«Узнавайте последние новости и общественное мнение. Введите: биржевой код»)

# инструмент памяти
    registry.register_function(memory_add_watchlist, "AddToWatchlist",
        "添加股票到关注列表。输入: '代码|名称' 如 '600519|贵州茅台'")
    registry.register_function(memory_remove_watchlist, "RemoveFromWatchlist",
«Удалите акцию из списка наблюдения. Введите: тикер»)
    registry.register_function(memory_get_watchlist, "GetWatchlist",
«Просмотреть текущий список наблюдения. Нет входных параметров»)
    registry.register_function(memory_save_analysis, "SaveAnalysis",
«Сохранить результаты анализа в историю. Введите: «Код|Проблема|Сводка»»)
    registry.register_function(memory_get_history, "GetHistory",
«Просмотреть историю анализа. Введите: код акции (необязательно)»)
    registry.register_function(memory_set_preference, "SetPreference",
«Установите пользовательские настройки. Введите: «ключ=значение», например, «Стиль=В основном технический анализ»»)
    registry.register_function(memory_get_preferences, "GetPreferences",
«Просмотр пользовательских настроек. Нет входных параметров»)

# Инструмент базы знаний RAG
    registry.register_function(rag_search, "SearchKnowledge",
«Выполните поиск в базе инвестиционных знаний (методы оценки/интерпретация технических индикаторов/принципы контроля рисков/правила доли A). Введите: ключевые слова запроса»)
    registry.register_function(rag_import, "ImportDocument",
«Импорт документов в базу знаний. Ввод: путь к файлу (.txt/.md)»)
    registry.register_function(rag_stats, "KnowledgeStats",
        "查看知识库统计信息")

#Инструмент управления контекстом
    registry.register_function(context_stats, "ContextStats",
«Просмотр текущего использования контекста разговора (использование токена/раунд)»)
    registry.register_function(context_clear, "ContextClear",
«Очистить контекст для начала нового сеанса. Нет входных параметров»).
    registry.register_function(context_summarize, "ContextSummarize",
«Вручную сжать контекст разговора. Входных параметров нет»).

    return registry


STOCK_SYSTEM_PROMPT = """你是专业股票分析助手 StockInsightAgent，具备完整认知能力的智能分析系统。

## Основные компетенции
- Получайте в режиме реального времени рыночные условия акций А, исторические K-линии, финансовые данные, технические индикаторы, новости и общественное мнение.
- Запомните список наблюдения пользователя, предпочтения анализа и записи исторического анализа.
- Запросить базу инвестиционных знаний (методы оценки, интерпретация технических индикаторов, принципы контроля рисков, правила торговли акциями А)
- Управление контекстом разговора (длинные разговоры автоматически сжимаются для обеспечения связности разговора)

## Функция памяти
- Когда пользователь говорит «Следить за акциями XX», используйте AddToWatchlist, чтобы добавить его в список наблюдения.
- После завершения анализа сохраните результаты анализа с помощью SaveAnaанализа.
- Используйте SetPreference, чтобы запомнить предпочтения, когда вы видите, что у пользователя есть четкие предпочтения в отношении инвестиционного стиля.
- 在分析新股票前，先查看 GetWatchlist 和 GetPreferences 了解用户背景

## Функция базы знаний
- 估值分析时可查询 SearchKnowledge 获取 PE/PB/PEG/股息率 等方法论
- При интерпретации технических индикаторов вы можете запросить SearchKnowledge, чтобы понять стандартные интерпретации, такие как MACD/RSI/полосы Боллинджера.
- При оценке риска вы можете запросить SearchKnowledge, чтобы получить информацию о принципах управления позициями и ограничения потерь.

## Управление контекстом
- Естественно ссылаться на ранее проанализированные выводы в ходе нескольких раундов диалога.
- Когда пользователь переключает объекты анализа, предыдущий анализ запаса будет связан
- Если контекст слишком длинный, система автоматически сжимает его, чтобы предотвратить потерю ключевой информации.

## Формат отчета об анализе
1. Базовый обзор 2. Технический анализ 3. Фундаментальные принципы и оценка 4. Новости 5. Предупреждение о рисках 6. Рекомендации по эксплуатации
Говорите правду, когда данные недоступны, и не выдумывайте ее. """


class FrameworkStockAgent:
    """基于 HelloAgents 框架 + Memory + RAG + Context 的股票分析 Agent"""

    def __init__(self):
        self.llm = self._build_llm()
        self.registry = build_tool_registry()
        self.ctx = get_context()

    def _build_llm(self):
        """构建 LLM，兼容 DeepSeek thinking mode 的 reasoning_content"""
        base = HelloAgentsLLM()
Reasoning_entries = [] # Сохраняем Reasoning_content каждого помощника по порядку

        try:
            adapter = base._adapter
            adapter._client = adapter.create_client()
            original_create = adapter._client.chat.completions.create

            def patched_create(*args, **kwargs):
                messages = kwargs.get("messages", [])
                # 注入 reasoning_content：给最近一条没有它的 assistant 消息
                missing_idx = 0
                fixed_msgs = []
                for m in messages:
                    m2 = dict(m)
                    if m2.get("role") == "assistant" and not m2.get("reasoning_content"):
                        if missing_idx < len(reasoning_entries):
                            m2["reasoning_content"] = reasoning_entries[missing_idx]
                        missing_idx += 1
                    fixed_msgs.append(m2)
                kwargs["messages"] = fixed_msgs
                resp = original_create(*args, **kwargs)
# Сохраняем новое Reasoning_content
                try:
                    msg = resp.choices[0].message
                    rc = getattr(msg, "reasoning_content", None)
                    if rc:
                        reasoning_entries.append(rc)
                except Exception:
                    pass
                return resp

            adapter._client.chat.completions.create = patched_create
        except Exception as e:
            print(f"Warning: _build_llm monkey patch failed, falling back to standard LLM: {e}")
        return base

    def _run_with_context(self, agent, question: str, mode: str):
"""Запуск агента и управление контекстом"""
        self.ctx.add_turn("user", question)
        result = agent.run(question)
        if result:
self.ctx.add_turn("assistant", result[:2000]) # Перехватываем результат, чтобы он не был слишком длинным
        print(f"\n  [{mode}] {self.ctx.get_stats()}")
        return result

    def react(self, question: str):
print(f"\n [режим кадра ReAct] {question}")
        agent = ReActAgent(
            name="StockReAct", llm=self.llm,
            tool_registry=self.registry,
            system_prompt=STOCK_SYSTEM_PROMPT, max_steps=6,
        )
        return self._run_with_context(agent, question, "ReAct")

    def plan_solve(self, question: str):
        print(f"\n  [PlanSolve 框架模式] {question}")
        agent = PlanSolveAgent(
            name="StockPlanner", llm=self.llm,
            tool_registry=self.registry,
            system_prompt=STOCK_SYSTEM_PROMPT,
            enable_tool_calling=True, max_tool_iterations=10,
        )
        return self._run_with_context(agent, question, "PlanSolve")

    def reflect(self, question: str):
print(f"\n [Режим рамки отражения] {question}")
        agent = ReflectionAgent(
            name="StockAnalyst", llm=self.llm,
            max_iterations=2, tool_registry=self.registry,
            enable_tool_calling=True, max_tool_iterations=8,
        )
        return self._run_with_context(agent, question, "Reflect")


# ===== CLI =====
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python framework_agent.py react '问题'")
        print("  python framework_agent.py plan '问题'")
        print("  python framework_agent.py reflect '问题'")
        sys.exit(1)

    mode = sys.argv[1]
вопрос = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Анализ недавней тенденции Kweichow Moutai 600519"

    agent = FrameworkStockAgent()
    if mode == "react":
        result = agent.react(question)
    elif mode == "plan":
        result = agent.plan_solve(question)
    elif mode == "reflect":
        result = agent.reflect(question)
    else:
print(f"Неизвестный режим: {mode}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(result)
