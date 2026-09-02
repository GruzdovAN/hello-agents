"""
Интеллектуальный помощник по анализу акций - помощник по диалогу с искусственным интеллектом (агент-координатор)

Анализируйте потребности пользователей, **разумно выбирайте субагента**, которого необходимо вызвать (не обязательно полностью настраивать),
Каждый субагент **непотоковое выполнение** после того, как координатор собирает все выходные данные:
1. Проанализируйте, какие результаты следует передать другим субагентам (например, инвестиционным консультантам нужны данные + общественное мнение)
2. Обобщить выходные данные субагента и передать их пользователю в потоковом формате.
"""

import sys
import os
import re
from pathlib import Path
from typing import Iterator, Optional

_PROJECT_ROOT = Path(__file__).parent.parent
_HELLO_PATH = _PROJECT_ROOT / "HelloAgents Optimized"
_BACKEND_DIR = _PROJECT_ROOT / "backend"
for p in [_HELLO_PATH, _BACKEND_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from hello_agents.core.llm import HelloAgentsLLM

from .text_truncation import truncate_at_natural_boundary

# Верхний предел вывода, когда координатор настраивает Агента (подсказка задачи + жесткое усечение)
COORD_DATA_MAX_CHARS = 2200
COORD_SENTIMENT_MAX_CHARS = 2200
COORD_ADVISOR_MAX_CHARS = 1600
COORD_MERGE_SECTION_MAX_CHARS = 2600
COORD_MERGE_OUTPUT_CHARS_HINT = 1000
# 整合步骤流式输出的 API max_tokens 上限（汉语约 1 token≈1~2 字，用于抑制冗长）
COORD_MERGE_MAX_TOKENS = 1400

# Маршрутизация: LLM должен сначала решить, звонить ли субагенту.
AGENT_SELECTION_PROMPT = """你是金融分析系统的「路由调度器」，只做一件事：判断是否需要调用后台分析 Agent。

Вызываемые модули (ключевые слова в нижнем регистре английского языка):
- данные: только тогда, когда пользователю явно нужны рыночные, финансовые, оценочные и фундаментальные данные.
- Настроения: только тогда, когда пользователю явно нужны новости, общественное мнение, объявления, исследовательские отчеты и настроения рынка.
- Советник: только тогда, когда пользователю явно нужен инвестиционный совет, рекомендации по покупке и продаже, а также советы по позиции.

Правила (обязательно прочитать):
1. Общение, научно-популярные вопросы и вопросы, не относящиеся к отдельным акциям → не отвечать только ни на один
2. Пользователь не указал биржевой код/название, и его невозможно определить → только ответ: нет
3. Пользователи спрашивают только об одном параметре → выберите только одно ключевое слово, не жадничайте на слишком много
4. Не выводить пояснения, Markdown или кавычки; не выводить слова, не включенные в список.

Можно вывести только одну из следующих восьми форм (вся строка, без других символов):
none
data
sentiment
advisor
data,sentiment
data,advisor
sentiment,advisor
data,sentiment,advisor

Пользовательский ввод:
{message}

Ваш вывод (одна строка): """


def coordinator_chat_stream(
    llm: HelloAgentsLLM,
    user_message: str,
    history: list,
    agent_system,
) -> Iterator[dict]:
    """
Интерфейс потоковой передачи AI-помощника по общению

процесс:
1. Проанализируйте намерение и разумно выберите субагента, которого нужно вызвать.
2. Вызовите выбранного субагента в режиме потоковой передачи и соберите полный вывод.
3. Если требуется инвестиционный консультант, передайте результаты работы других субагентов в качестве входных данных.
4. Координатор систематизирует весь вывод и возвращает его пользователю в потоковом формате.
    """
    yield {"type": "thinking", "content": "正在分析您的问题...\n"}

    stock_info = _extract_stock_info(user_message, history)

    # Step 1：仅一次 LLM 调用 — 决定是否启用子 Agent（避免无谓的全链路透传）
    yield {"type": "status", "content": "路由决策：正在判断是否调用分析引擎...\n"}
    agents_to_call = _select_agents(llm, user_message)
выход {"тип": "статус", "контент": f"Результат маршрута: {_agents_label(agents_to_call)}\n"}

    if not agents_to_call:
        yield from _handle_general(llm, user_message, history, agent_system, stock_info)
        yield {"type": "done"}
        return

    code = stock_info.get("code", "")
    name = stock_info.get("name", "")

    if not code:
        yield {"type": "thinking", "content": "请提供具体的股票代码或名称，我可以为您做更精准的分析。"}
        yield {"type": "done"}
        return

# Шаг 2. Вызов субагентов в порядке маршрутизации (с ограничением по количеству слов, чтобы отчет не растягивался до бесконечности)
    agent_results = {}
урожай {"type": "status", "content": "Последовательный вызов механизма анализа (с ограничением размера вывода)...\n"}

    if "data" in agents_to_call:
        yield {"type": "thinking", "content": "> 正在查询行情与财务数据...\n"}
        agent_results["data"] = agent_system.run_data_analysis(
            code, name, max_answer_chars=COORD_DATA_MAX_CHARS
        )
        yield {"type": "status", "content": "数据分析完成\n"}

    if "sentiment" in agents_to_call:
        yield {"type": "thinking", "content": "> 正在搜索资讯与分析舆情...\n"}
        agent_results["sentiment"] = agent_system.run_sentiment(
            code, name, max_answer_chars=COORD_SENTIMENT_MAX_CHARS
        )
        yield {"type": "status", "content": "舆情分析完成\n"}

# Шаг 3: Если вам нужен инвестиционный консультант, передайте ему данные + результаты общественного мнения
    if "advisor" in agents_to_call:
доходность {"type": "thinking", "content": "> Интеграция данных и общественного мнения для формирования инвестиционных предложений...\n"}
        advisor_input = _build_advisor_input(agent_results, code, name)
        agent_results["advisor"] = agent_system.run_advisor(
            advisor_input, max_answer_chars=COORD_ADVISOR_MAX_CHARS
        )
        yield {"type": "status", "content": "投资分析完成\n"}

# Шаг 4: Координатор организует вывод и возвращает его пользователю в потоковом формате.
    yield {"type": "status", "content": "\n---\n"}
    yield from _stream_aggregated_response(llm, user_message, agent_results, agents_to_call, code, name)

    if len(agent_results) > 1:
        yield {
            "type": "summary",
            "content": "以上为各分析引擎输出的整合结果，仅供参考，不构成投资建议。",
        }
    elif agent_results:
        yield {"type": "summary", "content": "分析已完成，仅供参考，不构成投资建议。"}
    yield {"type": "done"}


def _parse_route_line(raw: str) -> list[str]:
"""Результатом анализа маршрутизации LLM является упорядоченный и дедуплицированный список агентов."""
    if not raw:
        return []
    line = raw.strip().splitlines()[0].strip()
    line = re.sub(r"^[`\s]+|[`\s]+$", "", line)
    line = line.lower()
    if line.startswith("```"):
        line = re.sub(r"^```\w*", "", line).strip("`").strip()
# Удаляем общие префиксы
для префикса в ("выход:", "выход:", "ответ:", "агенты:", "список:", "список:"):
        if line.startswith(prefix):
            line = line[len(prefix) :].strip()
    tokens = [t.strip() for t in re.split(r"[,，;\s|]+", line) if t.strip()]
    order = ("data", "sentiment", "advisor")
    seen = set()
    out: list[str] = []
    for t in tokens:
        if t == "none":
            return []
        if t in order and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _select_agents(llm: HelloAgentsLLM, message: str) -> list[str]:
"""Одиночный звонок LLM: решите, звонить ли субагенту."""
    try:
        prompt = AGENT_SELECTION_PROMPT.format(message=message)
        result = llm.invoke(
            [
                {
                    "role": "system",
                    "content": "你只输出路由关键字行，禁止开场白与解释。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=48,
            temperature=0,
        )
        parsed = _parse_route_line(result or "")
        if parsed:
            return parsed
    except Exception:
        pass

# Вниз: ключевые слова (консервативно: старайтесь не вызывать полную ссылку)
если есть(kw в сообщении для kw в ["новости", "общественное мнение", "эмоции", "информация", "объявление", "отчет об исследовании"]):
        return ["sentiment"]
если есть (kw в сообщении для kw в ["Финансы", "Выручка", "Прибыль", "ROE", "PE", "Оценка", "Цитата", "Цена", "Вверх или вниз"]):
        return ["data"]
    if any(kw in message for kw in ["建议", "推荐", "买卖", "买入", "卖出", "投资建议"]):
        return ["advisor"]
    return []


def _build_advisor_input(agent_results: dict, code: str, name: str) -> str:
"""Интегрируйте результаты других субагентов во входные данные инвестиционного консультанта"""
    cap = COORD_MERGE_SECTION_MAX_CHARS
    parts = [
        f"请对股票 {name}({code}) 进行综合投资分析，以下是参考数据（可能已截断）：\n"
    ]

    if "data" in agent_results:
        data_text = agent_results["data"]
        parts.append(f"## 数据分析结果\n{data_text[:cap]}\n")

    if "sentiment" in agent_results:
        sent_text = agent_results["sentiment"]
        parts.append(f"## 舆情分析结果\n{sent_text[:cap]}\n")

    parts.append(
«Пожалуйста, дайте инвестиционный совет на основе приведенных выше данных: основные точки зрения, краткая логика, предупреждения о рисках, краткое изложение».
    )
    return "\n".join(parts)


def _stream_aggregated_response(
    llm: HelloAgentsLLM,
    message: str,
    agent_results: dict,
    agents_to_call: list[str],
    code: str,
    name: str,
) -> Iterator[dict]:
"""Координатор суммирует выходные данные субагента, а затем передает их в потоковом режиме"""

# Если есть только один агент, выведите результаты напрямую (при этом соблюдайте верхний предел слов для агента)
    if len(agents_to_call) == 1 and len(agent_results) == 1:
        key = agents_to_call[0]
        limit = {
            "data": COORD_DATA_MAX_CHARS,
            "sentiment": COORD_SENTIMENT_MAX_CHARS,
            "advisor": COORD_ADVISOR_MAX_CHARS,
        }.get(key, COORD_DATA_MAX_CHARS)
        result_text = list(agent_results.values())[0]
        yield {"type": "delta", "content": _hard_cap_text(result_text, limit)}
        return

# Несколько агентов: интеграция с помощью LLM
    stock_label = f"{name}({code})"

summary_prompt = f"""Вопрос пользователя: {message}

Ниже приведены выходные результаты каждого агента анализа для {stock_label}. Пожалуйста, объедините их в четкий ответ:

"""
    for agent_type, text in agent_results.items():
label_map = {"data": "анализ данных", "sentiment": "анализ общественного мнения", "советник": "инвестиционные советы"}
        label = label_map.get(agent_type, agent_type)
        body = (text or "").strip()
        if not body:
body = "(Это измерение не имеет выходных данных, возможно, истекло время ожидания или вызов не был успешным.)"
        body = _hard_cap_text(body, COORD_MERGE_SECTION_MAX_CHARS)
        summary_prompt += f"\n## {label}结果\n{body}\n"

    summary_prompt += f"""
Пожалуйста, объедините приведенные выше результаты и вывод со следующей структурой (общее количество слов в полном тексте должно контролироваться в пределах примерно {COORD_MERGE_OUTPUT_CHARS_HINT} китайских символов, и запрещено повторять большие разделы исходного текста):
1. Основные выводы (2–3 предложения)
2. Ключевые доказательства (2–4 балла по каждому параметру)
3. Комплексные предложения
4. Предупреждение о рисках
"""

    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是金融分析总结助手。输出务必简练，总篇幅控制在约 "
                    f"{COORD_MERGE_OUTPUT_CHARS_HINT} 个汉字内，避免堆砌重复。"
                ),
            },
            {"role": "user", "content": summary_prompt},
        ]
        for chunk in llm.stream_invoke(
            messages,
            max_tokens=COORD_MERGE_MAX_TOKENS,
            temperature=0.2,
        ):
            if chunk:
                yield {"type": "delta", "content": chunk}
    except Exception:
# Подведем итог: напрямую соединяем все результаты
        for agent_type, text in agent_results.items():
label_map = {"data": "анализ данных", "sentiment": "анализ общественного мнения", "советник": "инвестиционные советы"}
            label = label_map.get(agent_type, agent_type)
            capped = _hard_cap_text(text or "", COORD_MERGE_SECTION_MAX_CHARS)
            yield {"type": "delta", "content": f"\n## {label}\n{capped}\n"}


def _handle_general(
    llm: HelloAgentsLLM,
    message: str,
    history: list,
    agent_system,
    stock_info: dict,
) -> Iterator[dict]:
"""Ведение общих разговоров"""
    code = stock_info.get("code", "")
    name = stock_info.get("name", "")

# Если запасы упомянуты, но нет четких требований к анализу, дайте рекомендации.
    if code or name:
        stock_label = f"{name}({code})" if name else code
доходность {"type": "эмоциональный", "content": f"Я вижу, вы упомянули {stock_label}.\n\n"}
доходность {"type": "delta", "content": "Я могу сделать для вас:\n- проанализировать рыночные и финансовые данные по акциям\n- проверить мнения и информацию рынка\n- дать исчерпывающие инвестиционные предложения\n\nПожалуйста, скажите мне, какой аспект вы хотите знать?"}

    try:
messages = [{"role": "system", "content": "Вы дружелюбный ИИ-помощник по анализу акций. Пожалуйста, отвечайте пользователям лаконично и профессионально и помогайте пользователям формулировать конкретные потребности в анализе."}]
        for h in history[-6:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})

        for chunk in llm.stream_invoke(messages):
            if chunk:
                yield {"type": "delta", "content": chunk}
    except Exception:
доходность {"type": "delta", "content": "Вы можете спросить меня: проанализировать определенную акцию, проверить настроения рынка, получить инвестиционный совет и т. д. Пожалуйста, укажите конкретный код акции."}


def _extract_stock_info(message: str, history: list) -> dict:
"""Извлечение биржевой информации из сообщений"""
    info = {"code": "", "name": ""}

    code_match = re.search(r'[6|0|3]\d{5}', message)
    if code_match:
        info["code"] = code_match.group()

name_patterns = [r'Analyze (\S+)', r'(Kweichow Moutai | BYD | CATL | China Merchants Bank | Ping An of China | Wuliangye)']
    for pattern in name_patterns:
        name_match = re.search(pattern, message)
        if name_match:
            info["name"] = name_match.group(1)
            break

    return info


def _agents_label(agents: list[str]) -> str:
    labels = {"data": "数据分析", "sentiment": "舆情分析", "advisor": "投资顾问"}
return " + ".join(labels.get(a, a) для a в агентах), если агенты else "Нет необходимости вызывать агента"


def _hard_cap_text(text: str, max_chars: int) -> str:
"""Обрезайте слишком длинный текст (сначала абзацы/периоды), чтобы предотвратить расширение контекста модели в дальнейшем."""
    if max_chars <= 0 or not text:
        return text or ""
    t = text.strip()
    if len(t) <= max_chars:
        return t
    return truncate_at_natural_boundary(
t, max_chars, "\n\n…(Достигнут лимит слов координатора, продолжение будет пропущено)"
    )
