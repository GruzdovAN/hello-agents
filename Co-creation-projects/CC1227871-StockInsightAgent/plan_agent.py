"""Шаг 3: Многомерный анализ запасов «Планируй и решай»
Из главы 4 учебника hello-agents Парадигма Plan-and-Solve:
Планировщик: разбейте сложные задачи анализа на упорядоченные шаги.
Исполнитель: выполнять шаг за шагом, накапливать контекст и, наконец, создавать подробный отчет.
"""
import ast
from llm_client import HelloAgentsLLM
from tools import (
    get_realtime_quote, get_historical_data, get_financial_data,
    calc_indicators, get_news
)

PLANNER_PROMPT = """Вы — ведущий эксперт по планированию анализа запасов. Пользователь сделает запрос на анализ запасов, и ваша задача — разбить его на план анализа, состоящий из нескольких независимых шагов.

Каждый шаг должен быть сосредоточен на одном аспекте анализа и выстроен в логической последовательности от сбора данных до комплексного анализа.
可用数据维度: 实时行情、历史K线、技术指标(MA/MACD/RSI/布林带)、财务数据、新闻舆情。

Вопрос: {question}

Для вывода плана строго следуйте следующему формату. ```python и ``` необходимы в качестве префиксов и суффиксов:
```python
["Шаг 1: Описание конкретных действий", "Шаг 2: Описание конкретных действий", ...]
```

Пример:
```python
[«Получите рыночную информацию 600519 в реальном времени и 60-дневную историческую K-линию», «Рассчитайте технические индикаторы для оценки тенденций и динамики», «Получите финансовые данные для оценки стоимости», «Получите новости и общественное мнение для оценки настроений рынка», «Соберите все данные и выведите полный аналитический отчет»]
```
"""

EXECUTOR_PROMPT = """Вы профессиональный биржевой аналитик. Вы анализируете акции шаг за шагом по заранее заданному плану.

## Полный план:
{plan}

## Результаты выполненных шагов:
{history}

## Текущие шаги:
{current_step}

## Доступные инструменты
- GetRealtimeQuote: получайте котировки в реальном времени. Ввод: биржевой код
- GetHistoricalData: получить историческую K-линию. Формат ввода: «код|ежедневно|количество дней»
- CalcIndicators: расчет технических индикаторов. Формат ввода: «код|ежедневно|количество дней»
- GetFinancialData: получение финансовых данных. Ввод: биржевой код
- GetNews: узнавайте новости и общественное мнение. Ввод: биржевой код

Пожалуйста, следуйте текущим шагам. Если вам необходимо получить данные, в ответе четко укажите инструмент и параметры, которые будут вызываться, в формате:
[[ИНСТРУМЕНТ:Имя инструмента:Параметры]]

Пример:
[[TOOL:GetRealtimeQuote:600519]]
[[TOOL:GetHistoricalData:600519|daily|60]]

Если текущий шаг представляет собой комплексный анализ (нет необходимости получать новые данные), предоставьте анализ, основанный непосредственно на существующих результатах.
如果这是最后一步，请输出完整的综合分析报告，包含: 基本概况、技术面、基本面、消息面、风险提示、投资建议。

Пожалуйста, выполните текущие шаги сейчас. """


class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list:
        prompt = PLANNER_PROMPT.format(question=question)
        messages = [{"role": "user", "content": prompt}]

print("\n [Планирование...]")
        response = self.llm_client.think(messages=messages) or ""

        try:
            plan_str = response.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            if isinstance(plan, list) and len(plan) > 0:
                return plan
        except (ValueError, SyntaxError, IndexError) as e:
print(f" [Ошибка анализа плана: {e}]")

# Резервный вариант: план анализа по умолчанию
        return [
«Получите рыночные условия в реальном времени и исторические данные K-line за 60 дней»,
«Расчет технических индикаторов (MACD/RSI/Полосы Боллинджера/Скользящее среднее)»,
«Получить финансовые данные для оценки фундаментальных показателей и оценок»,
«Получите новости и общественное мнение, чтобы понять настроения рынка»,
«Синтезируйте все данные для создания полного аналитического отчета»
        ]


class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
# Сопоставление инструментов
        self.tools = {
            "GetRealtimeQuote": get_realtime_quote,
            "GetHistoricalData": get_historical_data,
            "CalcIndicators": calc_indicators,
            "GetFinancialData": get_financial_data,
            "GetNews": get_news,
        }

    def execute(self, question: str, plan: list) -> str:
        import re
        history = ""
        final_result = ""

print(f"\n [В плане {len(plan)} шагов]")
        for i, step in enumerate(plan, 1):
            print(f"\n{'='*50}")
            print(f"  步骤 {i}/{len(plan)}: {step}")
            print(f"{'='*50}")

            prompt = EXECUTOR_PROMPT.format(
                plan="\n".join([f"{j}. {s}" for j, s in enumerate(plan, 1)]),
                history=history if history else "（尚无已完成步骤）",
                current_step=step,
            )
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.think(messages=messages) or ""
print(f" [LLM 响应]\n{response[:500]}{'...' if len(response)>500 else ''}")

# Вызов инструмента синтаксического анализа [[TOOL:Name:args]]
            tool_pattern = re.findall(r"\[\[TOOL:(\w+):(.*?)\]\]", response)
            tool_results = []

            for tool_name, tool_args in tool_pattern:
                func = self.tools.get(tool_name)
                if func:
                    result = func(tool_args.strip())
                    tool_results.append(f"[{tool_name}结果]\n{result}")
                    print(f"  [工具] {tool_name} 执行完成")

# Если есть вызов инструмента, позвольте LLM ответить еще раз на основе результатов инструмента.
            if tool_results:
Followup = f"Результаты выполнения инструмента:\n\n" + "\n\n".join(tool_results)
                followup += f"\n\n请基于以上数据完成当前步骤: {step}"
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": followup})
                final_response = self.llm_client.think(messages=messages) or ""
                step_result = final_response
            else:
                step_result = response

print(f" [результат шага {i}]\n{step_result[:300]}{'...' if len(step_result)>300 else ''}")

            history += f"\n--- 步骤{i}: {step} ---\n{step_result}\n"
            final_result = step_result

        return final_result


class PlanAndSolveStockAgent:
"""Агент анализа запасов "Планируй и решай"""

    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(llm_client)
        self.executor = Executor(llm_client)

    def run(self, question: str):
        print(f"\n{'='*60}")
print(f"Режим планирования и решения")
print(f" Вопрос: {question}")
        print(f"{'='*60}")

№ 1. Планирование
        plan = self.planner.plan(question)
print(f"\n План анализа:")
        for i, step in enumerate(plan, 1):
            print(f"    {i}. {step}")

# 2. Выполнить
        final_answer = self.executor.execute(question, plan)

        print(f"\n{'='*60}")
print(f"Анализ завершен")
        print(f"{'='*60}")
        return final_answer
