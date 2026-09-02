"""Step 2: StockInsightAgent — ReAct 范式智能股票分析助手"""
import re
from llm_client import HelloAgentsLLM
from tools import (
    ToolExecutor, get_realtime_quote, get_historical_data,
    get_financial_data, calc_indicators, get_news
)

STOCK_AGENT_PROMPT = """
Вы — профессиональный помощник по анализу акций StockInsightAgent. Вы можете получить котировки акций A в реальном времени, исторические K-линии,
Финансовые отчеты, технические индикаторы, новости и общественное мнение, а затем объединить эту информацию, чтобы дать аналитические выводы.

Доступны следующие инструменты:
{tools}

Просьба отвечать строго в следующем формате:

Мысль: ваш мыслительный процесс, анализ потребностей пользователей и планирование следующих шагов.
Действие: Действие, которое вы решите предпринять, должно быть в одном из следующих форматов:
- `{{tool_name}}[{{tool_input}}]`: вызов доступного инструмента.
Описание формата ввода инструмента:
- Котировки в реальном времени: код акции или аббревиатура акции, например «600519» или «Kweichow Moutai».
- Историческая K-линия: «код|период|дни», например «600519|ежедневно|60».
- Финансовые данные: код акции, например «600519».
- Технические индикаторы: «код|период|дни», например «600519|ежедневно|120».
- Новости и мнения: код акции, например «600519».
- «Готово [Окончательный отчет об анализе]»: когда вы собрали достаточно информации, чтобы иметь возможность вывести полный отчет об анализе.

Формат аналитического отчета должен содержать:
1. Базовый обзор акций (последняя цена, увеличение или уменьшение, рыночная стоимость и т. д.)
2. Технический анализ (тренд, скользящая средняя, ​​MACD, RSI, уровень поддержки и давления)
3. Фундаментальный анализ (интерпретация финансовых показателей)
4. Новости (последние новости и общественное мнение)
5. Предупреждение о рисках
6. Подробное резюме

важный:
- Вызывайте только один инструмент одновременно
- Если пользователь указывает только имя, но не код, код можно найти путем поиска котировок в реальном времени по имени.
- Вывод полного отчета об анализе Markdown после сбора достаточной информации.
- Если данные ненормальны, сообщайте об этом правдиво и не выдумывайте.

Теперь начните анализировать:
Question: {question}
History: {history}
"""


class StockInsightAgent:
"""Интеллектуальный агент анализа акций — ReAct Paradigm"""

    def __init__(self, llm_client: HelloAgentsLLM, max_steps: int = 8):
        self.llm_client = llm_client
        self.tool_executor = ToolExecutor()
        self.max_steps = max_steps
        self.history = []

# Зарегистрируйте 5 инструментов анализа
        print("注册工具:")
        self.tool_executor.registerTool(
            "GetRealtimeQuote",
            "获取实时行情(最新价/涨跌幅/成交量/PE/市值)。输入: 股票代码或简称",
            get_realtime_quote
        )
        self.tool_executor.registerTool(
            "GetHistoricalData",
            "获取历史K线(OHLCV)。输入格式: '代码|周期|天数'，周期=daily/weekly/monthly",
            get_historical_data
        )
        self.tool_executor.registerTool(
            "GetFinancialData",
            "获取财务指标(ROE/ROA/毛利率/营收增长等)。输入: 股票代码",
            get_financial_data
        )
        self.tool_executor.registerTool(
            "CalcIndicators",
            "计算技术指标(MA/MACD/RSI/布林带/支撑压力位)。输入格式: '代码|周期|天数'",
            calc_indicators
        )
        self.tool_executor.registerTool(
            "GetNews",
«Получите последние новости и общественное мнение. Введите: биржевой код»,
            get_news
        )
        print()

    def run(self, question: str):
        self.history = []
        current_step = 0

        print(f"\n{'='*60}")
print(f" [пользователь]: {question}")
        print(f"{'='*60}")

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step}/{self.max_steps} 步 ---")

            tools_desc = self.tool_executor.getAvailableTools()
History_str = "\n".join(self.history) if self.history else "(первое выполнение, без истории)"
            prompt = STOCK_AGENT_PROMPT.format(
                tools=tools_desc, question=question, history=history_str
            )

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
print("LLM не вернул действительный ответ.")
                break

            thought, action = self._parse_output(response_text)
            if thought:
print(f" [мысль] {thought}")
            if not action:
print("Не удалось выполнить действие, процесс завершен.")
                break

            if action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                print(f"\n{'='*60}")
print(f" [Отчет об анализе]")
                print(f"{'='*60}")
                print(final_answer)
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name:
                self.history.append("Observation: Action 格式无效。")
                continue

print(f" [行动] {tool_name}[{tool_input[:60]}{'...' if len(tool_input)>60 else ''}]")
            tool_func = self.tool_executor.getTool(tool_name)
            observation = (
                tool_func(tool_input) if tool_func
else f «Ошибка: инструмент «{tool_name}» не найден»
            )
print(f" [观察]\n{observation[:300]}{'...' if len(str(observation))>300 else ''}")

            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print(f"\n  已达到最大步数 ({self.max_steps})，流程终止。")
        return None

    def _parse_output(self, text: str):
        # 支持 Thought: / **Thought:** / Thought： 等多种格式
        thought_match = re.search(
            r"(?:\*\*)?Thought(?:\*\*)?\s*[:：]\s*(.*?)(?=\n(?:\*\*)?Action(?:\*\*)?\s*[:：]|$)",
            text, re.DOTALL | re.IGNORECASE
        )
        action_match = re.search(
            r"(?:\*\*)?Action(?:\*\*)?\s*[:：]\s*(.*?)$",
            text, re.DOTALL | re.IGNORECASE
        )
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
# Очистка обратных кавычек уценки
        if action:
            action = action.strip("`\"' \n\r")
        return thought, action

    def _parse_action(self, action_text: str):
# Очистите обратные кавычки, жирный шрифт уценки и т. д.
        clean = action_text.strip("`\"' \n\r*_")
        match = re.match(r"(\w+)\[(.*)\]", clean, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parse_action_input(self, action_text: str):
        clean = action_text.strip("`\"' \n\r*_")
        match = re.match(r"\w+\[(.*)\]", clean, re.DOTALL)
        return match.group(1) if match else ""
