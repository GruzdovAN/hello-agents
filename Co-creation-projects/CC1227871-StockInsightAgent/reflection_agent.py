"""Шаг 4. Режим отражения - самопроверка и оптимизация аналитических отчетов.
Из учебника hello-agents, глава 4 «Парадигма отражения»:
Первоначальный анализ -> Анализ и обзор -> Оптимизация и улучшение -> Циклически до тех пор, пока улучшение не перестанет требоваться.
"""
from typing import List, Dict, Any
from llm_client import HelloAgentsLLM
from tools import (
    get_realtime_quote, get_historical_data, get_financial_data,
    calc_indicators, get_news
)


class Memory:
"""Кратковременная память: хранение следов анализа (первичный отчет + рефлексия + отчет об улучшении)"""
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        self.records.append({"type": record_type, "content": content})
print(f" [Память] Добавлена ​​запись '{record_type}'")

    def get_trajectory(self) -> str:
        parts = []
        for r in self.records:
            label = "分析报告" if r['type'] == 'execution' else "评审意见"
            parts.append(f"--- {label} ---\n{r['content']}")
        return "\n\n".join(parts)

    def get_last_execution(self) -> str:
        for r in reversed(self.records):
            if r['type'] == 'execution':
                return r['content']
        return None


# ===== Подскажите шаблон слова =====

INITIAL_ANALYSIS_PROMPT = """你是资深股票分析师。请对以下股票进行全面分析。

## Доступные данные
{data_section}

## Требования к анализу
{task}

Пожалуйста, выведите отчет структурированного анализа, включающий:
1. Базовый обзор и оценка тенденций
2. Технический анализ (тренды, скользящие средние, индикаторы, ключевые цены)
3. Фундаментальный и оценочный анализ
4. Новости и настроения рынка
5. Предупреждение о рисках
6. Краткосрочные, среднесрочные и долгосрочные предложения по эксплуатации.
"""

REFLECTION_PROMPT = """你是极其严格的股票投资评审专家。你的任务是审查以下分析报告，找出缺陷和遗漏。

## Требования к исходному анализу
{task}

## Отчет подлежит рассмотрению
{report}

## Просмотр размеров
1. **Целостность данных**: отсутствуют ли ключевые параметры данных? Есть ли ошибки интерпретации данных?
2. **风险覆盖**: 是否遗漏了重要风险因素？（如：行业政策风险、汇率风险、大股东减持、解禁压力）
3. **Логическая последовательность**. Последовательны ли технические/фундаментальные/новостные выводы? Есть ли внутреннее противоречие?
4. **Проверка слепых зон**. Есть ли какие-либо углы обзора, которые не были учтены? (Например: верхние и нижние звенья производственной цепочки, межрыночные связи, потоки капитала)
5. **Обратное мышление**: если окончательное суждение будет бычьим, пожалуйста, бросьте вызов с медвежьей точки зрения; наоборот. Возможно ли, что решение было ошибочным?

Пожалуйста, оставляйте комментарии к обзору напрямую и укажите как минимум на 3 конкретных недостатка или упущения.
Если отчет об анализе является всеобъемлющим, строгим и не имеет явных упущений, ответьте: «Улучшений не требуется».
"""

REFINE_PROMPT = """你是资深股票分析师。评审专家指出了你上一轮分析报告的缺陷。

## Исходные требования
{task}

## Ваш последний раунд отчетов
{previous_report}

## Просмотр комментариев
{reflection}

Пожалуйста, создайте улучшенный и полный аналитический отчет на основе комментариев обзора. Для решения проблем, отмеченных рецензентами, необходимо провести специальный дополнительный анализ и исправления.
Вывести полную улучшенную версию отчета (структура 6 глав остается неизменной, но содержание должно отражать улучшения после размышлений).
"""


class ReflectionStockAgent:
"""Отражающий анализ запасов Агент — Анализ→Обзор→Цикл улучшения"""

    TOOLS = {
        "GetRealtimeQuote": get_realtime_quote,
        "GetHistoricalData": get_historical_data,
        "CalcIndicators": calc_indicators,
        "GetFinancialData": get_financial_data,
        "GetNews": get_news,
    }

    def __init__(self, llm_client: HelloAgentsLLM, max_iterations: int = 2):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations

    def run(self, task: str):
        print(f"\n{'='*60}")
        print(f"  Reflection 反思模式 (最多{self.max_iterations}轮)")
print(f" вопрос: {task}")
        print(f"{'='*60}")

# --- Этап 1: Автоматический сбор данных ---
print("\n[Фаза 1] Автоматический сбор данных...")
        data_text = self._collect_data(task)

# --- Этап 2: Первоначальный анализ ---
print(f"\n [Фаза 2] Создание отчета о первоначальном анализе...")
        initial_prompt = INITIAL_ANALYSIS_PROMPT.format(
            data_section=data_text, task=task
        )
        messages = [{"role": "user", "content": initial_prompt}]
        initial_report = self.llm_client.think(messages=messages) or ""
        self.memory.add_record("execution", initial_report)
        print(f"  [初始报告] 已生成 ({len(initial_report)} 字)")

# --- Фаза 3: Цикл размышлений-совершенствования ---
        for iteration in range(self.max_iterations):
print(f"\n [Фаза 3] {итерация+1}/{self.max_iterations} раунд размышлений...")

# обзор
            reflect_prompt = REFLECTION_PROMPT.format(
                task=task, report=self.memory.get_last_execution()
            )
            messages = [{"role": "user", "content": reflect_prompt}]
            feedback = self.llm_client.think(messages=messages) or ""
            self.memory.add_record("reflection", feedback)

#Проверяем сходимость
если в отзыве «улучшение не требуется»:
print("\n В отчете [обзора] нет очевидных недостатков, и анализ окончен.")
                break

# Улучшение
print(f"\n [Этап 3] Улучшение отчета на основе комментариев рецензентов...")
            refine_prompt = REFINE_PROMPT.format(
                task=task,
                previous_report=self.memory.get_last_execution(),
                reflection=feedback,
            )
            messages = [{"role": "user", "content": refine_prompt}]
            refined_report = self.llm_client.think(messages=messages) or ""
            self.memory.add_record("execution", refined_report)
            print(f"  [改进报告] 已生成 ({len(refined_report)} 字)")

# --- Вывод итогового отчета ---
        final_report = self.memory.get_last_execution()
        print(f"\n{'='*60}")
print(f"Окончательный отчет об анализе (после {sum(1 for r в self.memory.records if r['type']=='reflection')} раунда отражения)")
        print(f"{'='*60}")
        print(final_report)
        return final_report

    def _collect_data(self, task: str) -> str:
"""Автоматически извлекайте биржевые коды из задач и собирайте ключевые данные"""
        import re

#Извлекаем биржевой код
        codes = re.findall(r"\b(\d{6})\b", task)
        if not codes:
return «(Код акции не может быть распознан автоматически, пожалуйста, укажите в вопросе 6-значный код)»

        code = codes[0]
        parts = []

# Котировки в реальном времени
print(f" [Коллекция] Котировки в реальном времени {code}...")
        r = self.TOOLS["GetRealtimeQuote"](code)
parts.append(f"### Котировки в реальном времени\n{r}")

# Историческая K-линия (60 дней)
print(f" [Коллекция] 60-дневная K-линия {code}...")
        r = self.TOOLS["GetHistoricalData"](f"{code}|daily|60")
parts.append(f"### 60-дневная историческая K-линия\n{r}")

# Технические индикаторы (120 дней)
print(f" [Коллекция] Технические индикаторы {code}...")
        r = self.TOOLS["CalcIndicators"](f"{code}|daily|120")
parts.append(f"### Технические индикаторы\n{r}")

# финансовые данные
print(f" [Коллекция] Финансовые данные {code}...")
        r = self.TOOLS["GetFinancialData"](code)
parts.append(f"### Финансовые данные\n{r}")

# новости
print(f" [Коллекция] Новости и общественное мнение {code}...")
        r = self.TOOLS["GetNews"](code)
parts.append(f"### Новости и общественное мнение\n{r}")

        return "\n\n".join(parts)
