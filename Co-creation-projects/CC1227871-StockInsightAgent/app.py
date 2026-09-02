"""StockInsightAgent — интерфейс Gradio"""
import threading
import queue
import gradio as gr
from framework_agent import FrameworkStockAgent
from memory import (
    memory_get_watchlist, memory_add_watchlist, memory_remove_watchlist,
    memory_get_history, memory_get_preferences,
)
from rag import rag_import, rag_stats

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = FrameworkStockAgent()
    return _agent


def _run_with_capture(q: queue.Queue, agent, mode: str, msg: str):
    import io, sys
    import contextlib
    buffer = io.StringIO()

    class QueueWriter:
        def __init__(self, original_stdout):
            self.original = original_stdout
            # Ensure _local exists for threads
            import threading
            self._local = threading.local()

        @property
        def is_active(self):
            return getattr(self._local, "active", False)

        @is_active.setter
        def is_active(self, value):
            self._local.active = value

        def write(self, s):
            if self.is_active:
                buffer.write(s)
                q.put(s)
            else:
                self.original.write(s)

        def flush(self):
            if not self.is_active:
                self.original.flush()

    if not isinstance(sys.stdout, QueueWriter):
        sys.stdout = QueueWriter(sys.stdout)

    sys.stdout.is_active = True
    try:
if mode == "Углубленный анализ (PlanSolve)":
            result = agent.plan_solve(msg)
elif mode == "Критический анализ (Размышление)":
            result = agent.reflect(msg)
        else:
            result = agent.react(msg)
    except Exception as e:
result = f"Ошибка анализа: {e}"
    finally:
        sys.stdout.is_active = False
    q.put(None)
    q.result = result or ""


def respond_stream(message: str, history: list, mode: str, agent=None):
    if agent is None:
        agent = get_agent()

    if not message or not message.strip():
        yield history, "", agent
        return

    msg = message.strip()
    history = history or []

#──Команда быстрого доступа──
    quick = {
(«помощь», «помощь», «?»): лямбда: HELP_TEXT,
(«список», «список наблюдения»): Memory_get_watchlist,
(«история»,): Memory_get_history,
(«предпочтения»,): Memory_get_preferences,
(«База знаний»,): rag_stats,
    }
    for keys, handler in quick.items():
        if msg in keys:
            history.append({"role": "user", "content": msg})
            history.append({"role": "assistant", "content": handler()})
            yield history, "", agent
            return

если msg.startswith("Следовать"):
        parts = msg[3:].strip().split()
        c, n = parts[0], (parts[1] if len(parts) > 1 else "")
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": memory_add_watchlist(f"{c}|{n}")})
        yield history, "", agent
        return

если msg.startswith("удалить"):
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": memory_remove_watchlist(msg[3:].strip())})
        yield history, "", agent
        return

если msg.startswith("История "):
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": memory_get_history(msg[3:].strip())})
        yield history, "", agent
        return

если msg.startswith("импорт"):
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": rag_import(msg[3:].strip()) + "\n" + rag_stats()})
        yield history, "", agent
        return

# ── Потоковый анализ ──
    history.append({"role": "user", "content": msg})
    history.append({"role": "assistant", "content": "..."})

    q = queue.Queue()
    t = threading.Thread(target=_run_with_capture, args=(q, agent, mode, msg), daemon=True)
    t.start()

    collected = []
    while True:
        try:
            chunk = q.get(timeout=0.3)
        except queue.Empty:
            if collected:
                history[-1]["content"] = "".join(collected)
            yield history, "", agent
            continue
        if chunk is None:
            break
        collected.append(chunk)
        history[-1]["content"] = "".join(collected)
        yield history, "", agent

    final = getattr(q, 'result', '') or "".join(collected)
    history[-1]["content"] = str(final)
    yield history, "", agent


HELP_TEXT = """## Руководство пользователя

### Анализ акций
Прямой ввод: «Анализ оценки и риска Kweichow Moutai 600519».

### Следуйте указаниям руководства
| Команда | Описание |
|------|------|
| `список` | Посмотреть список наблюдения |
| `Следуйте за 600519 Мутай` | Добавить подписку |
| `Удалить 600519` | Удалить следующее |

### Запрос данных
| Команда | Описание |
|------|------|
| `История` | Вся история анализа |
| `Предпочтения` | Настройки пользователя |
| `База знаний` | Статус базы знаний |"""

# ===== Пользовательский CSS =====
CUSTOM_CSS = """
/* глобальный */
.gradio-container {
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif !important;
}

/* Скрыть нижний колонтитул по умолчанию */
footer { display: none !important; }

/* Header */
.header-wrap {
    background: linear-gradient(135deg, #0f1729 0%, #1a2744 50%, #0d2137 100%);
    border-bottom: 2px solid #2a5c8a;
    padding: 16px 32px;
}
.header-wrap h1 {
    font-size: 26px;
    font-weight: 700;
    color: #e8f0fe;
    margin: 0;
    letter-spacing: -0.5px;
}
.header-wrap .subtitle {
    font-size: 13px;
    color: #7b9bcb;
    margin-top: 4px;
}
.header-wrap .status-row {
    display: flex;
    gap: 16px;
    margin-top: 10px;
    flex-wrap: wrap;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 12px;
    font-weight: 500;
}
.status-badge.online {
    background: rgba(34, 197, 94, 0.15);
    color: #4ade80;
}
.status-badge.data {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
}

/* Карточка боковой панели */
.sidebar-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
}
.sidebar-card h4 {
    font-size: 12px;
    font-weight: 600;
    color: #7b9bcb;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 0 10px 0;
}

/* Основная диалоговая область */
.main-chat {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    background: rgba(255,255,255,0.02) !important;
}

/* Поле ввода */
.input-box textarea {
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    background: rgba(255,255,255,0.04) !important;
    color: #e0e0e0 !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
}
.input-box textarea::placeholder {
    color: rgba(255,255,255,0.3) !important;
}

/* кнопка */
button.primary {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    transition: all 0.2s !important;
    height: 100% !important;
    min-height: 44px !important;
}
button.primary:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
}
button.secondary {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #6aaff7 !important;
    font-size: 12px !important;
    padding: 8px 14px !important;
    transition: all 0.2s !important;
    width: 100% !important;
    text-align: left !important;
}
button.secondary:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #c8d6e5 !important;
    border-color: rgba(255,255,255,0.18) !important;
}

/* Выбор режима радио */
.mode-radio-wrap {
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 14px 16px;
    border: 1px solid rgba(255,255,255,0.08);
}

/* --- Восстановление высокой контрастности --- */

/* Метка радио/флажка — ярко-синяя */
.radio-option label, .radio-option span,
label:has(input[type="radio"]), .radio-label,
fieldset label, .radio-wrap label {
    color: #6aaff7 !important;
}
/* Наведение радио — ярко-серый */
.radio-option:hover label, .radio-option:hover span,
fieldset label:hover, .radio-wrap:hover label {
    color: #c8d6e5 !important;
}
/* Выбрано радио — жирный и белый */
input[type="radio"]:checked + label,
input[type="radio"]:checked ~ span {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Поле ввода */
input[type="text"], textarea, .input-box textarea {
    background: #1a2236 !important;
    border: 1px solid #3a5078 !important;
    color: #e8edf5 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
}
input[type="text"]:focus, textarea:focus {
    border-color: #4a8cf7 !important;
    box-shadow: 0 0 0 3px rgba(74, 140, 247, 0.15) !important;
    outline: none !important;
}
input[type="text"]::placeholder, textarea::placeholder {
    color: #5a7099 !important;
}

/* выбор раскрывающегося списка */
select, .dropdown {
    background: #1a2236 !important;
    color: #d0d8e8 !important;
    border: 1px solid #3a5078 !important;
}

/* Связь */
a, .examples a {
    color: #7aabf7 !important;
}
a:hover {
    color: #a0c4ff !important;
}

/* Содержимое всплывающей подсказки чата */
.message-row .message {
    color: #e4eaf5 !important;
}

/* Облако чата */
.bubble-wrap { border-radius: 12px !important; }

/* Значок ярлыка */
.quick-icon {
    font-size: 16px;
    margin-right: 6px;
}

/* полоса прокрутки */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
"""

# ===== Интерфейс =====
with gr.Blocks(title="StockInsightAgent") as app:

    # ── Header ──
    gr.HTML("""
    <div class="header-wrap">
        <h1>StockInsightAgent</h1>
<div class="subtitle">Интеллектуальный помощник по анализу акций</div>
        <div class="status-row">
            <span class="status-badge online">&#9679; 系统就绪</span>
<span class="status-badge data">&#9679; Источник данных: Oriental Fortune/Sina/Tencent</span>
        </div>
    </div>
    """)

    with gr.Row(equal_height=True):
# ── Левый столбец ──
        with gr.Column(scale=1, min_width=200):
            gr.HTML('<div class="sidebar-card"><h4>分析模式</h4></div>')
            mode_radio = gr.Radio(
choice=["Быстрый анализ (ReAct)", "Углубленный анализ (PlanSolve)", "Критический анализ (Размышление)"],
value="Быстрый анализ (ReAct)",
                label="",
                interactive=True,
            )

            gr.HTML('<div class="sidebar-card"><h4>快捷操作</h4></div>')
btn_watchlist = gr.Button("Список наблюдения", elem_classes="вторичный")
            btn_history = gr.Button("分析历史", elem_classes="secondary")
            btn_kb = gr.Button("知识库状态", elem_classes="secondary")
            btn_prefs = gr.Button("用户偏好", elem_classes="secondary")

            gr.HTML("""
            <div style="margin-top:16px; font-size:11px; color:#5a7a9a; line-height:1.6;">
Введите <b>help</b>, чтобы увидеть больше команд<br>
            </div>
            """)

# ── Основная область ──
        with gr.Column(scale=4):
            agent_state = gr.State(None)

            chatbot = gr.Chatbot(
                label="",
                height=520,
                elem_classes="main-chat",
                placeholder="<div style='text-align:center; color:#6a8aaa; padding-top:80px;'>"
                             "<div style='font-size:48px; margin-bottom:16px;'>📊</div>"
"<div style='font-size:16px; font-weight:600;'>Начните анализировать свое портфолио</div>"
"<div style='font-size:13px;margin-top:8px;'>Введите код или название акции, чтобы получить подробный аналитический отчет</div>"
                             "</div>",
            )

            with gr.Row(equal_height=True):
                msg_input = gr.Textbox(
Placeholder="Введите вопрос для анализа...",
                    label="",
                    scale=6,
                    elem_classes="input-box",
                )
submit_btn = gr.Button("Начать анализ", вариант="первичный", elem_classes="первичный", масштаб=1)

#──Привязка событий──
    msg_input.submit(
        fn=respond_stream,
        inputs=[msg_input, chatbot, mode_radio, agent_state],
        outputs=[chatbot, msg_input, agent_state],
    )
    submit_btn.click(
        fn=respond_stream,
        inputs=[msg_input, chatbot, mode_radio, agent_state],
        outputs=[chatbot, msg_input, agent_state],
    )

    def quick_action(action, history, agent):
        for result in respond_stream(action, history, "快速分析 (ReAct)", agent):
            pass
        return result[0], result[2]

btn_watchlist.click(lambda h, a: fast_action("列表", h, a), [чат-бот, агент_состояние], [чат-бот, агент_состояние])
btn_history.click(lambda h, a: fast_action("历史", h, a), [чат-бот, агент_состояние], [чат-бот, агент_состояние])
    btn_kb.click(lambda h, a: quick_action("知识库", h, a), [chatbot, agent_state], [chatbot, agent_state])
btn_prefs.click(lambda h, a: fast_action("偏好", h, a), [чат-бот, агент_состояние], [чат-бот, агент_состояние])

if __name__ == "__main__":
    app.launch(
        server_name="127.0.0.1", server_port=7861, share=False,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
    )
