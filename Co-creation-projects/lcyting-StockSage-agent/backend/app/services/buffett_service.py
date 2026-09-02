"""
Интеллектуальный помощник по анализу акций — уровень службы оценки инвестиций Баффета

Загрузите справочные документы Баффета по инвестиционному мышлению и создайте систему оценки стоимости инвестиций.
Для вызовов уровня маршрутизации API и уровня агента.
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

# Убедитесь, что путь навыков можно импортировать
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/app/services -> project root
_AGENTS_DIR = _PROJECT_ROOT / "agents"
_BUFFETT_DIR = _PROJECT_ROOT/"навыки"/"инвестиционное мышление Баффета"/"навыки"/"баффет"

for p in [_AGENTS_DIR, str(_PROJECT_ROOT)]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agents.text_truncation import truncate_at_natural_boundary
from app.config import settings


# ====================================================================
# Основное содержание инвестиционного мышления Баффета (краткое изложение взято из справочных документов)
# ====================================================================

BUFFETT_FRAMEWORK = {
    "quick_filter": {
"name": "Быстрый фильтр на 8 вопросов",
        "questions": [
«Круг компетенции: можете ли вы объяснить в одном абзаце, как эта компания зарабатывает деньги?»,
«Настойчивость: останется ли компания более конкурентоспособной через 10 лет?»,
«Рвы: могут ли конкуренты усердно работать, чтобы повторить свои основные сильные стороны?»,
«Ценовая сила: можно ли повысить цены на 5–10% без потери большого количества клиентов?»,
«Качество прибыли: действительно ли прибыль переводится в денежные средства (а не в бухгалтерские трюки)?»,
«Долговая безопасность: сможете ли вы пережить худший сценарий развития отрасли (выручка -30%)?»,
«Честность управления: честно ли руководство говорит о проблемах, а не скрывает их?»,
«Разумная цена: достаточно ли велик разрыв между текущей ценой и внутренней стоимостью?»,
        ],
"rule": "2 "нет" требует веской причины; 4 "нет" отказывайтесь сразу",
    },
    "moat_analysis": {
"name": "Анализ рва",
        "types": [
«Преимущество в издержках (лидерство в издержках, экономия за счет масштаба)»,
«Издержки переключения (затраты на миграцию клиентов высоки)»,
«Сетевой эффект (чем больше пользователей, тем больше ценность)»,
«Нематериальные активы (бренды, патенты, франшизы)»,
«Эффективный масштаб (естественная монополия, небольшая доля рынка)»,
        ],
"judment": "Смотрите не только на текущий статус, но, что более важно, на тенденцию (расширение/стабилизация/сужение)",
    },
    "management_assessment": {
"name": "Три измерения управленческой оценки",
        "dimensions": [
«Честность (пункт автоматического отклонения: немедленно сдавайтесь, если обнаружите нечестность)»,
            "资本配置能力（能否明智分配资本：再投资/收购/回购/分红）",
«Менталитет собственника (думаете ли вы как собственник и не тратите деньги акционеров)»,
        ],
        "warning": "警惕制度迫力——优秀的管理层在制度压力下也可能做出不合理决策",
    },
    "financial_metrics": {
"name": "Финансовые показатели",
        "metrics": [
            "所有者收益 = 净利润 + 折旧摊销 - 维护性资本支出 - 营运资金增加",
«Средняя цель ROIC за 10 лет > 15%»,
«Целевой коэффициент конверсии наличных> 90%»,
«Проверочная прибыль (с учетом нераспределенной прибыли инвестируемой компании)»,
        ],
    },
    "valuation": {
"name": "Оценка и запас прочности",
        "methods": [
«Дисконтированный денежный поток (DCF)»,
«Метод мультипликации прибыли (разумный диапазон PE)»,
«Метод оценки активов (переоценка чистых активов)»,
        ],
        "margin_of_safety": {
«Высокая уверенность (широкий ров + прогнозируемый рост)»: «20-30%»,
«В целом отлично»: «30-40%»,
«Есть неопределенности»: «40-50%»,
«Невозможно достоверно оценить»: «Не инвестировать»,
        },
    },
    "risk_analysis": {
"name": "Классификация рисков",
        "categories": {
«Структурный риск»: «Сужение рва, технологические сбои, ужесточение нормативных требований»,
«Финансовый риск»: «Чрезмерное кредитное плечо, мошенничество с денежными потоками, внебалансовые обязательства»,
«Риск поведения»: «Предвзятость подтверждения, невозвратные издержки, институциональные силы»,
        },
    },
    "sell_criteria": {
"name": "Четыре критерия продажи",
        "criteria": [
«Серьезно завышенная цена (намного выше внутренней стоимости)»,
«Основной ров разрушен»,
«У руководства проблемы с честностью (продать немедленно)»,
«Откройте для себя значительно лучшие инвестиционные возможности»,
        ],
    },
}

# Описание системы комплексной оценки
BUFFETT_FRAMEWORK_DESC = """
## Система оценки стоимостных инвестиций Баффета

### Основная философия
- **Внутренняя стоимость > Рыночная цена → Запас прочности**: покупайте только те акции, цены которых значительно ниже их внутренней стоимости.
- **Ров > Всё**: устойчивое конкурентное преимущество — основа долгосрочной прибыли.
- **Принцип круга компетенции**: инвестируйте только в тот бизнес, который вы понимаете.
- **Мистер. Рынок**: Рынок служит вам, а не направляет вас
- **ДОЛГОСРОЧНОЕ ДЕРЖАНИЕ**: думайте о 10-летней перспективе, а не о цене акций в следующем квартале.

### Процесс оценки
1. **Быстрая проверка** — проверка из 8 вопросов (завершение в течение 2 минут).
2. **Качество предприятия** — Тип рва + Тенденция, оценка руководства
3. **Финансовый снимок** — рентабельность инвестиций, конверсия денежных средств, доходы владельца.
4. **Анализ стоимости** — Расчет диапазона внутренней стоимости и запаса прочности.
5. **Оценка рисков** — Три типа рисков: структурные/финансовые/поведенческие.
6. **Комплексное решение** — покупать/не покупать/держать/продавать + рекомендуемая цена покупки.
"""


def _mx_cell_to_str(v: Any) -> str:
"""Замечательные ячейки таблицы преобразуются в сериализуемые строки JSON."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if v != v:  # NaN
            return ""
    if isinstance(v, (str, int, float)):
        return str(v)
    return str(v)


def _first_table_row_key_values(block: Optional[dict], max_keys: int = 48) -> dict:
    """取 mx_data 风格结果中首张表首行，扁平为字符串字典（减小体积、避免不可序列化对象）。"""
    if not isinstance(block, dict) or not block.get("success"):
        return {"success": False, "fields": {}}
    tables = block.get("tables") or []
    fields: dict[str, str] = {}
    for t in tables[:1]:
        names: List[str] = list(t.get("fieldnames") or t.get("fieldNames") or [])
        rows = t.get("rows") or []
        if not rows:
            continue
        row = rows[0]
        if isinstance(row, dict):
            for k, v in list(row.items())[:max_keys]:
                fields[str(k)] = _mx_cell_to_str(v)
        elif isinstance(row, list) and names:
            for i, name in enumerate(names):
                if i >= max_keys:
                    break
                val = row[i] if i < len(row) else None
                fields[str(name)] = _mx_cell_to_str(val)
        break
    return {"success": True, "fields": fields}


def slim_evaluation_context_for_api(full: dict) -> dict:
"""Ответ HTTP: удалить гигантские таблицы, сохранить фреймы и рыночные/финансовые сводки."""
    if not isinstance(full, dict):
        return {}
    return {
        "framework": full.get("framework"),
        "framework_description": full.get("framework_description"),
        "market_snapshot": _first_table_row_key_values(full.get("market_data")),
        "financial_snapshot": _first_table_row_key_values(full.get("financial_data")),
    }


def get_buffett_framework() -> dict:
"""Получите систему оценки инвестиций Баффета.

Вернитесь к полной архитектуре инвестиционного мышления Баффета, включая:
- Быстро отфильтровать свой список
- Структура анализа рвов
- Аспекты управленческой оценки
- Шаблоны финансовых показателей
- Оценка и расчет запаса прочности
- Классификация оценки риска
- критерии продажи

    Returns:
        {
            "success": True,
"framework": {...}, # Полная структура оценки
"description": str, #Описание кадра
        }
    """
    return {
        "success": True,
        "framework": BUFFETT_FRAMEWORK,
        "description": BUFFETT_FRAMEWORK_DESC,
    }


def evaluate_with_buffett(stock_code: str, stock_name: str = "", data_context: dict = None) -> dict:
«»»Используйте инвестиционное мышление Баффета для оценки акций

Соберите данные анализа и создайте контекст оценки Buffett Framework, возвращая пакеты данных, необходимые для оценки.

    Args:
stock_code: 6-значный код акции
stock_name: название акции
        data_context: 已有的分析数据（可选），包含行情/财务/概况/舆情信息

    Returns:
        {
            "success": True/False,
            "stock_code": str,
            "stock_name": str,
            "evaluation_context": {
                "framework": dict,     # 巴菲特评估框架
"market_data": dict, # Рыночные данные
"financial_data": dict,# финансовые данные
"profile_data": dict, # Профиль компании
"sentiment_data": dict,# данные общественного мнения
            },
"report_template": str, # Шаблон отчета об оценке
            "error": str or None
        }
    """
    result = {
        "success": False,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "evaluation_context": {},
        "report_template": "",
        "error": None,
    }

    data_context = data_context or {}

# Создаем контекст оценки
    context = {
        "framework": BUFFETT_FRAMEWORK,
        "framework_description": BUFFETT_FRAMEWORK_DESC,
        "market_data": data_context.get("market", {}),
        "financial_data": data_context.get("financial", {}),
        "profile_data": data_context.get("profile", {}),
        "sentiment_data": data_context.get("sentiment", {}),
    }

    result["success"] = True
    result["evaluation_context"] = context
    result["report_template"] = _build_buffett_report_template(stock_code, stock_name)

    return result


def _build_buffett_report_template(stock_code: str, stock_name: str) -> str:
"""Создать шаблон отчета об оценке в стиле Баффета

    Args:
stock_code: 6-значный код акции
stock_name: название акции

    Returns:
Шаблон отчета в формате Markdown
    """
    name_display = stock_name or stock_code

    template = f"""
# Отчет Баффета об оценке стоимостных инвестиций

## Цель: {name_display} ({stock_code})

---

## 1. Заключение

[Покупать/Не покупать/Продолжать наблюдать/Держать/Продавать] — основная причина в одном предложении.

---

## 2. Оценка круга компетенции

[Четкое суждение: внутри круга/вне круга/граничной области]
Если вы находитесь вне круга: перестаньте анализировать и честно объясните, почему.

---

## 3. Ключевые предположения (3-5 пунктов)

[Перечислите основные предположения, на которых основаны решения, для последующей проверки]
1.
2.
3.
4.
5.

---

## 4. Быстрый отбор (проверка по 8 вопросам)

| # | Размеры | Результат | Описание |
|---|------|------|------|
| 1 | Круг компетенции | [Да/Нет] | |
| 2 | Настойчивость | [Да/Нет] | |
| 3 | 护城河 | [是/否] | |
| 4 | Ценовая власть | [Да/Нет] | |
| 5 | Качество дохода | [Да/Нет] | |
| 6 | Долговое обеспечение | [Да/Нет] | |
| 7 | Честность управления | [Да/Нет] | |
| 8 | Разумная цена | [Да/Нет] | |

---

## 5. Анализ качества предприятия

### Ров
- **Тип**: [Ценовое преимущество/Затраты на переход/Сетевой эффект/Нематериальные активы/Эффективное масштабирование]
- **Сила**: [Сильный/Средний/Слабый]
- **趋势**: [拓宽/稳定/变窄]

### Управление
- **Честность**: [Оценка]
- **资本配置能力**: [评估]
- **Менталитет владельца**: [Оценка]

### Бизнес-модель
- **Тип**: [Франшиза/Товар/Гибрид]

### Предупреждение о принудительном использовании системы
- [да/нет] — [основание]

---

## 6. Финансовый снимок

| Индикаторы | Ценности | Оценка |
|------|------|------|
| ROIC (среднее за 10 лет) | — | |
| Курс обмена наличных | — | |
| Долговое обеспечение | — | |
| Оценка доходов владельца | — | |

---

## 7. Анализ оценки

- **Диапазон внутренних значений**: —
- **Текущий запас прочности**: —% (уровень достоверности: высокий/средний/низкий)
- **Рекомендуемая цена покупки**: —

---

## 8. Проверьте критерии продажи один за другим

| # | Стандарт | Решение | Основа |
|---|------|------|------|
| 1 | Серьезно завышена цена? | [Да/Нет] | |
| 2 | Разрушен ли фундаментальный ров? | [Да/Нет] | |
| 3 | Проблемы с целостностью управления? | [Да/Нет] | |
| 4 | Есть ли больше шансов? | [Да/Нет] | |

---

## 9. Основные риски (до 3)

1. **Риск 1**: [Описание]
2. **Риск 2**: [Описание]
3. **Риск третий**: [Описание]

---

## 10. Индикаторы мониторинга

### Ежеквартальная проверка:
- [Индикатор 1]
- [Показатель 2]

### Вызов сигнала на продажу:
- [Сигнал 1]
- [Сигнал 2]

---

## 11. Всеобъемлющее решение

[Непосредственное изложение предложений по принятию решений и основных причин с точки зрения и тона Баффета]

---

> ⚠️ Приведенный выше анализ основан на концепции стоимостного инвестирования Баффета, предназначен только для справки и не является инвестиционным советом. Инвестиции рискованны, поэтому будьте осторожны при входе на рынок.
"""
    return template


def _truncate_text(s: str, max_len: int) -> str:
    if not s:
        return ""
    if len(s) <= max_len:
        return s
    return truncate_at_natural_boundary(s, max_len, "\n\n…（内容过长已截断）")


def _ensure_hello_agents_path() -> None:
    _hello = _PROJECT_ROOT / "HelloAgents Optimized"
    if str(_hello) not in sys.path:
        sys.path.insert(0, str(_hello))


def make_buffett_llm_client():
"""Создание клиента LLM для создания длинных статей Баффета (потоковое/непотоковое совместное использование)."""
    _ensure_hello_agents_path()
    from hello_agents.core.llm import HelloAgentsLLM

    buffett_llm_timeout = max(int(settings.LLM_TIMEOUT), 180)
    return HelloAgentsLLM(
        model=settings.LLM_MODEL_ID,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL or None,
        provider=os.getenv("LLM_PROVIDER", "auto"),
        temperature=0.35,
        max_tokens=6144,
        timeout=buffett_llm_timeout,
    )


def prepare_buffett_ai_messages(stock_code: str, stock_name: str = "") -> Dict[str, Any]:
"""Агрегируйте рыночное/финансовое/общественное мнение и собирайте сообщения LLM.

    Returns:
        成功: {"ok": True, "messages": [...], "name": str}
        失败: {"ok": False, "error": str}
    """
    if not settings.is_agent_ready():
        return {
            "ok": False,
            "error": "未配置有效的 LLM_API_KEY，无法一键生成 AI 评估报告",
        }

    code = (stock_code or "").strip()
    if len(code) < 4:
        return {"ok": False, "error": "请输入有效的股票代码"}

    try:
        from app.services.market_service import (
            get_stock_financial,
            get_stock_profile,
            get_stock_quote,
        )
        from app.services.news_service import analyze_sentiment
        from app.services.analysis_service import _extract_stock_name, _format_data_section

        quote_data = get_stock_quote(code)
        financial_data = get_stock_financial(code)
        profile_data = get_stock_profile(code)
        sentiment_data = analyze_sentiment(code)

        name = (stock_name or "").strip() or _extract_stock_name(profile_data) or code

        chunks = []
        if quote_data.get("success"):
chunks.append("### Quote\n" + _format_data_section(quote_data))
        else:
            chunks.append(
                "### 行情\n获取失败: " + str(quote_data.get("error") or "未知错误")
            )

        if financial_data.get("success"):
chunks.append("\n### 财务\n" + _format_data_section(financial_data))
        else:
            chunks.append(
                "\n### 财务\n获取失败: " + str(financial_data.get("error") or "未知错误")
            )

        if profile_data.get("success"):
chunks.append("\n### Профиль компании\n" + _format_data_section(profile_data))
        else:
            chunks.append(
                "\n### 公司概况\n获取失败: " + str(profile_data.get("error") or "未知错误")
            )

        if sentiment_data.get("success"):
            news_items = sentiment_data.get("news_items") or []
            report_items = sentiment_data.get("report_items") or []
            ann_items = sentiment_data.get("announce_items") or []
            chunks.append(
f"\n### Сводка общественного мнения\nНовости {len(news_items)} / Отчет об исследовании {len(report_items)} / Объявление {len(ann_items)}"
            )
            merged = (news_items + report_items + ann_items)[:12]
            for item in merged:
                title = item.get("title") or ""
                date = (item.get("date") or "").split()[0] if item.get("date") else ""
                chunks.append(f"- [{date}] {title}")
        else:
            chunks.append(
                "\n### 舆情\n获取失败: " + str(sentiment_data.get("error") or "未知错误")
            )

        data_bundle = _truncate_text("\n".join(chunks), 14000)
        framework_desc = _truncate_text(BUFFETT_FRAMEWORK_DESC.strip(), 5000)
        outline = _build_buffett_report_template(code, name)

        user_prompt = f"""请撰写完整的《巴菲特价值投资评估报告》（Markdown）。

Тема: **{name}** (биржевой код {code})

[Структура отчета и ключевые моменты, которые необходимо охватить]
以下提纲中的章节结构与顺序必须体现在你的输出中（使用 ## / ### 标题）；每个章节需要实质性段落或列表，禁止只输出标题或空白占位。

{outline}

【价值投资框架参考】（按需引用，勿全文照搬）
{framework_desc}

【客观数据】（结论必须以此为依据，勿编造数据中不存在的精确数值）
{data_bundle}

Требования к написанию:
1. 「结论」「综合判断」中必须明确：**买入 / 不买 / 持续观察 / 持有 / 卖出** 之一，并附简短理由。
2. «Быстрый фильтр» предоставляет суждения и краткую информацию по одному по 8 измерениям.
3. Оценка и запас прочности: Если данные недостаточно количественные, объясните их качественно и перечислите информацию, которую необходимо дополнить. Не изготавливайте PE/PB.
4. Отдельная строка в конце статьи: ⚠️Приведённый выше анализ носит справочный характер и не является инвестиционной рекомендацией. Инвестиции рискованны, поэтому будьте осторожны при входе на рынок.
"""

        system = (
«Вы старший аналитик по инвестициям в ценные бумаги и хорошо разбираетесь в методах стоимостного инвестирования Баффета и Грэма».
«Вы выводите только текст Markdown, и ваш тон профессиональный и разумный».
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ]
        return {"ok": True, "messages": messages, "name": name}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def iter_buffett_ai_report_events(stock_code: str, stock_name: str = "") -> Iterator[Dict[str, Any]]:
    """供 NDJSON 流式响应：通过巴菲特评估Agent (ReflectionAgent) 生成报告。"""
    prep = prepare_buffett_ai_messages(stock_code, stock_name)
    if not prep.get("ok"):
        yield {"type": "error", "message": prep.get("error") or "准备失败"}
        return

    code = (stock_code or "").strip()
    name = prep.get("name") or code
    yield {"type": "meta", "stock_code": code, "stock_name": name}

    try:
        from agents.advisor_agent import evaluate_buffett_stream

        for event in evaluate_buffett_stream(
            stock_code=code,
            stock_name=name,
        ):
            yield event

        yield {"type": "done"}
    except Exception as e:
        yield {"type": "error", "message": str(e)}


def generate_buffett_ai_report(stock_code: str, stock_name: str = "") -> dict:
    """调用 LLM 生成填充后的巴菲特风格 Markdown 报告（同步阻塞，请在 asyncio.to_thread 中调用）。

    Returns:
        {"success": bool, "report_markdown": str | None, "error": str | None}
    """
    result: dict = {"success": False, "report_markdown": None, "error": None}

    prep = prepare_buffett_ai_messages(stock_code, stock_name)
    if not prep.get("ok"):
        result["error"] = prep.get("error") or "准备失败"
        return result

    try:
        llm = make_buffett_llm_client()
        md = llm.invoke(
            prep["messages"],
            max_tokens=6144,
            temperature=0.35,
        )
        md = (md or "").strip()
        if not md:
result["error"] = "LLM вернулся пустым, повторите попытку позже"
            return result

        result["success"] = True
        result["report_markdown"] = md
        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def load_buffett_reference(ref_name: str) -> Optional[str]:
"""Загрузить содержимое указанного справочного файла Баффета.

    Args:
ref_name: имя справочного файла, например «03-business-moat».

    Returns:
        文件内容文本，若文件不存在返回 None
    """
    safe_name = ref_name.replace("..", "").replace("\\", "").replace("/", "")
    ref_path = _BUFFETT_DIR / "references" / f"{safe_name}.md"

    if not ref_path.exists():
        return None

    try:
        with open(ref_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None
