"""
PaperAssistant — интеллектуальный ассистент по статьям, Gradio Web-интерфейс

Предоставляет поиск литературы, резюме статей, генерацию цитат, редактуру, создание плана и извлечение PDF.
Все действия записываются в журнал диалогов для просмотра.
"""
import os
import sys
import json
from datetime import datetime
import gradio as gr

from dotenv import load_dotenv
load_dotenv()

# Совместимость Windows UTF-8
sys.stdout.reconfigure(encoding='utf-8')

from hello_agents import (
    HelloAgentsLLM, SimpleAgent, ToolRegistry, Config
)
from src.arxiv_tool import ArxivSearchTool
from src.pdf_tool import PDFExtractTool
from src.citation_tool import CitationTool
from src.literature_tool import LiteratureSearchTool
from src.pubmed_tool import PubMedSearchTool
from src.crossref_tool import CrossRefSearchTool
from src.openalex_tool import OpenAlexSearchTool
from src.aminer_tool import AminerSearchTool


# ========================================
# Система журнала диалогов
# ========================================
HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "conversations")

class ConversationLogger:
    """Менеджер журнала диалогов: запись, сохранение и поиск всех взаимодействий"""

    def __init__(self, save_dir=HISTORY_DIR):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.records = self._load_all()

    def _filepath(self):
        """Файл журнала текущей сессии"""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.save_dir, f"session_{today}.json")

    def _load_all(self):
        """Загрузить всю историю"""
        records = []
        if os.path.exists(self.save_dir):
            for fname in sorted(os.listdir(self.save_dir), reverse=True):
                if fname.endswith(".json"):
                    fpath = os.path.join(self.save_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            records.extend(json.load(f))
                    except Exception:
                        pass
        return records

    def add(self, tab, action, user_input, output):
        """Добавить запись диалога и сохранить"""
        record = {
            "id": len(self.records) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tab": tab,
            "action": action,
            "user_input": user_input[:200] + ("..." if len(user_input) > 200 else ""),
            "output_preview": output[:200] + ("..." if len(output) > 200 else ""),
            "output_full": output
        }
        self.records.insert(0, record)  # Новые записи в начале

        # Добавить в файл за сегодня
        today_file = self._filepath()
        try:
            existing = []
            if os.path.exists(today_file):
                with open(today_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.insert(0, record)
            with open(today_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return record

    def format_history_html(self):
        """Форматировать в HTML; у каждой записи кнопка удаления"""
        if not self.records:
            return "<p><i>Записей диалога пока нет — после использования они сохранятся автоматически.</i></p>"

        lines = [f'<p style="color:#888;">Всего записей: {len(self.records)}</p>']
        for r in self.records[:50]:
            escaped_output = (r['output_full']
                             .replace("&", "&amp;")
                             .replace("<", "&lt;")
                             .replace(">", "&gt;")
                             .replace("\n", "<br>")
                             .replace("`", "&#96;"))
            rid = r["id"]
            lines.append(f'''
<div style="border:1px solid #e0e0e0; border-radius:8px; padding:12px; margin:10px 0; position:relative;">
  <div style="position:absolute; top:8px; right:8px;">
    <button onclick="document.getElementById('del_trigger').querySelector('textarea,input').value='{rid}';
                     document.getElementById('del_trigger').querySelector('textarea,input').dispatchEvent(new Event('input',{{bubbles:true}}));
                     document.getElementById('del_trigger').querySelector('textarea,input').dispatchEvent(new Event('change',{{bubbles:true}}));"
            style="background:#e74c3c; color:#fff; border:none; border-radius:4px; cursor:pointer; padding:4px 12px; font-size:12px;">
      ✕ Удалить
    </button>
  </div>
  <div style="margin-right:70px;">
    <strong>[#{r['id']}] {r['timestamp']}</strong>
    <span style="color:#666;"> | {r['tab']} | {r['action']}</span>
    <p style="margin:6px 0 2px 0; color:#555; font-size:13px;"><b>Ввод:</b> {r['user_input']}</p>
    <details style="margin-top:6px;">
      <summary style="cursor:pointer; color:#2980b9;">Показать полный вывод</summary>
      <div style="background:#f8f9fa; padding:10px; border-radius:4px; margin-top:4px; max-height:300px; overflow-y:auto; font-size:13px; white-space:pre-wrap;">{escaped_output}</div>
    </details>
  </div>
</div>''')
        return "\n".join(lines)

    def delete_record(self, record_id: int) -> str:
        """Удалить одну запись"""
        for i, r in enumerate(self.records):
            if r.get("id") == record_id:
                del self.records[i]
                # Повторно сохранить файл за текущий день
                today_file = self._filepath()
                try:
                    with open(today_file, "w", encoding="utf-8") as f:
                        json.dump(self.records, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                return f"Запись удалена #{record_id}"
        return f"Запись не найдена #{record_id}"

    def clear(self):
        """Очистить записи"""
        self.records = []
        for fname in os.listdir(self.save_dir):
            if fname.endswith(".json"):
                os.remove(os.path.join(self.save_dir, fname))
        return "Журнал диалогов очищен."


# Глобальный экземпляр журнала
logger = ConversationLogger()


# ========================================
# Менеджер сессий (история диалогов редактуры и плана)
# ========================================
class ChatSessionManager:
    """Управление многораундовыми сессиями редактуры и плана"""

    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def _filepath(self, session_id: str) -> str:
        return os.path.join(self.save_dir, f"{session_id}.json")

    def save(self, session_id: str, messages: list, title: str = ""):
        """Сохранить сессию"""
        data = {
            "id": session_id,
            "title": title or f"Сессии {session_id[:8]}",
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": messages
        }
        with open(self._filepath(session_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, session_id: str) -> list:
        """Загрузить сессию, вернуть список messages"""
        with open(self._filepath(session_id), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("messages", [])

    def list_sessions(self):
        """Список всех сессий [(id, title, updated), ...]"""
        sessions = []
        if os.path.exists(self.save_dir):
            for fname in sorted(os.listdir(self.save_dir), reverse=True):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(self.save_dir, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        sessions.append((
                            data.get("id", fname[:-5]),
                            data.get("title", fname[:-5]),
                            data.get("updated", "")
                        ))
                    except Exception:
                        pass
        return sessions

    def delete(self, session_id: str):
        """Удалить сессию"""
        path = self._filepath(session_id)
        if os.path.exists(path):
            os.remove(path)


# Отдельный менеджер сессий для редактуры и плана
polish_sessions = ChatSessionManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "polish_sessions"))
outline_sessions = ChatSessionManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "outline_sessions"))
paper_sessions = ChatSessionManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "paper_sessions"))


# ========================================
# Инициализация: LLM + инструменты + агенты
# ========================================
config = Config(trace_enabled=False)
llm = HelloAgentsLLM()

tool_registry = ToolRegistry()
tool_registry.register_tool(LiteratureSearchTool())
tool_registry.register_tool(ArxivSearchTool())
tool_registry.register_tool(PubMedSearchTool())
tool_registry.register_tool(CrossRefSearchTool())
tool_registry.register_tool(OpenAlexSearchTool())
tool_registry.register_tool(AminerSearchTool())
tool_registry.register_tool(PDFExtractTool())
tool_registry.register_tool(CitationTool())

# ---- Агент поиска литературы ----
search_agent = SimpleAgent(
    name="Помощник поиска литературы", llm=llm, config=config,
    system_prompt="""Вы — эксперт по академическому поиску литературы. У вас 6 инструментов поиска; строго вызывайте инструмент с именем, указанным пользователем:

- literature_search: Semantic Scholar, все дисциплины (рекомендуется)
- aminer_search: AMiner, китайскоязычные академические статьи
- openalex_search: OpenAlex, открытый доступ
- pubmed_search: PubMed, биомедицина
- crossref_search: CrossRef, метаданные журнальных статей
- arxiv_search: arXiv, препринты CS/математики/физики

Правила:
1. Для поиска статей используйте только инструмент, указанный пользователем; не заменяйте другим
2. Анализируйте и рекомендуйте на основе реальных результатов инструмента
3. Категорически запрещено выдумывать информацию о статьях при ошибке вызова инструмента
4. При ошибке инструмента сообщайте об ошибке пользователю напрямую"""
)
# Зарегистрировать все 6 инструментов поиска
search_agent.add_tool(tool_registry.get_tool("literature_search"))
search_agent.add_tool(tool_registry.get_tool("openalex_search"))
search_agent.add_tool(tool_registry.get_tool("pubmed_search"))
search_agent.add_tool(tool_registry.get_tool("crossref_search"))
search_agent.add_tool(tool_registry.get_tool("arxiv_search"))
search_agent.add_tool(tool_registry.get_tool("aminer_search"))

# ---- Агент резюме статьи ----
summary_agent = SimpleAgent(
    name="Помощник резюме статьи", llm=llm, config=config,
    system_prompt="""Вы — эксперт по рецензированию академических статей. Сформируйте отчёт-резюме по структуре:

## Информация о статье
## Исследовательский вопрос
## Методы и новизна
## Вклад и ограничения
## Выводы и перспективы

Используйте русский язык для отчёта; профессиональные термины можно оставлять на английском."""
)

# ---- Фабрика диалоговых агентов (новый экземпляр на диалог) ----

def create_polish_agent():
    """Создать диалогового агента редактуры"""
    return SimpleAgent(
        name="Помощник редактуры статей", llm=llm, config=config,
        system_prompt="""Вы — опытный редактор академических текстов. Помогайте пользователю редактировать статью в диалоге.

Принципы редактуры:
1. Сохранять исходный смысл, улучшать только формулировки
2. Улучшать структуру предложений, убирать избыточность
3. Обеспечивать логическую связность и единообразие терминов
4. Кратко пояснять причины правок

Формат диалога: пользователь может несколько раз уточнять требования (например, «более формально», «сократить третий абзац»);
запоминайте предыдущий контент и историю правок и продолжайте оптимизацию на этой основе."""
    )

def create_outline_agent():
    """Создать диалогового агента плана"""
    return SimpleAgent(
        name="Помощник генерации плана", llm=llm, config=config,
        system_prompt="""Вы — опытный академический наставник. Помогайте пользователю составить план статьи в диалоге.

Вам нужно:
1. Разбить тему на ключевые главы и подтемы
2. Для каждой главы спланировать основные пункты содержания
3. Рекомендовать методы исследования и примеры литературы

Формат диалога: пользователь может просить корректировки (например, «добавить сравнение экспериментов в третью главу», «детализировать обзор литературы»);
запоминайте уже сгенерированный план и вносите изменения, а не начинайте заново каждый раз."""
    )

def create_paper_writer_agent():
    """Создать диалогового агента написания (с поиском литературы)"""
    agent = SimpleAgent(
        name="Помощник написания статей", llm=llm, config=config,
        system_prompt="""Вы — эксперт по написанию академических статей. У вас 6 инструментов поиска литературы:

- literature_search: Semantic Scholar, поиск по всем дисциплинам (рекомендуется в первую очередь)
- aminer_search: AMiner, китайскоязычные академические статьи
- openalex_search: OpenAlex, открытый доступ
- pubmed_search: PubMed, биомедицинская литература
- crossref_search: CrossRef, журнальные статьи
- arxiv_search: arXiv, препринты

Правила написания (строго соблюдать):
1. По предоставленному плану писать статью главу за главой
2. Академический стиль, строгая логика, чёткие абзацы
3. **При цитировании сначала ищите реальные статьи через инструменты поиска; цитируйте только реальные результаты**
4. Для каждой цитаты указывайте в списке литературы реальные данные (автор, заголовок, год, журнал)
5. **Категорически запрещено** выдумывать несуществующие заголовки, авторов или журналы
6. При ошибке поиска сообщайте пользователю «ошибка поиска литературы в этой области, повторите позже», а не выдумывайте источники"""
    )
    # Зарегистрировать все инструменты поиска для достоверных источников
    for name in ["literature_search", "openalex_search", "pubmed_search",
                 "crossref_search", "arxiv_search", "aminer_search"]:
        agent.add_tool(tool_registry.get_tool(name))
    return agent


# ========================================
# Callback Gradio (все действия логируются)
# ========================================

def search_papers(query, source, max_results, field, year_from, year_to):
    """Поиск литературы — 5 источников"""
    if not query.strip():
        return "Введите ключевые слова."

    # Источник данных → имя инструмента
    SOURCE_MAP = {
        "Semantic Scholar": "literature_search",
        "AMiner": "aminer_search",
        "OpenAlex": "openalex_search",
        "PubMed": "pubmed_search",
        "CrossRef": "crossref_search",
        "arXiv": "arxiv_search",
    }
    tool_name = next((v for k, v in SOURCE_MAP.items() if source.startswith(k)), "literature_search")
    source_name = next((k for k in SOURCE_MAP if source.startswith(k)), "Semantic Scholar")

    # Параметры (расширенные фильтры: Semantic Scholar, OpenAlex, PubMed, CrossRef)
    params_str = f"max_results={int(max_results)}"
    supports_advanced = source_name in ("Semantic Scholar", "OpenAlex", "PubMed", "CrossRef")
    if supports_advanced and field and field != "Все области":
        params_str += f", field='{field}'"
    if supports_advanced and year_from and year_from.strip():
        params_str += f", year_from='{year_from.strip()}'"
    if supports_advanced and year_to and year_to.strip():
        params_str += f", year_to='{year_to.strip()}'"

    try:
        result = search_agent.run(
            f"Используйте {tool_name} инструмент для поискастатей по теме，затем проанализируйтерезультат：{query}\n"
            f"параметры: {params_str}"
        )
        logger.add("Поиск литературы", f"{source_name} поиск статей", query, result)
        return result
    except Exception as e:
        err = f"ошибка поиска: {str(e)}"
        logger.add("Поиск литературы", f"{source_name} ошибка поиска", query, err)
        return err


def summarize_paper(content):
    """Резюме статьи"""
    if not content.strip():
        return "Введите содержание статьи."
    try:
        result = summary_agent.run(f"Структурированное резюме следующего содержания статьи：\n\n{content}")
        logger.add("Резюме статьи", "структурированное резюме", content, result)
        return result
    except Exception as e:
        err = f"Ошибка резюме: {str(e)}"
        logger.add("Резюме статьи", "ошибка резюме", content, err)
        return err


def generate_citation(title, authors, journal, year, volume, pages, doi, fmt):
    """Генерация цитаты"""
    if not title.strip() or not authors.strip():
        return "Укажите как минимум название и авторов."
    user_input = f"{title} | {authors} | {journal} | {year} | формат: {fmt}"
    try:
        params = {
            "title": title, "authors": authors,
            "journal": journal, "year": year,
            "volume": volume, "pages": pages, "doi": doi,
            "format": fmt
        }
        resp = tool_registry.execute_tool("citation_generator", json.dumps(params))
        logger.add("Генерация цитаты", f"цитата в формате {fmt}", user_input, resp.text)
        return resp.text
    except Exception as e:
        err = f"ошибка генерации: {str(e)}"
        logger.add("Генерация цитаты", "ошибка генерации", user_input, err)
        return err


def polish_chat(message, history, session_id):
    """Диалог редактуры статьи — многоходовый, автосохранение сессии"""
    if not message.strip():
        return "", history, session_id, _polish_sessions_dropdown()

    # Для новой сессии автоматически генерируется ID
    if not session_id:
        session_id = f"polish_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        context = ""
        for msg in history:
            role = "пользователь" if msg["role"] == "user" else "ассистент"
            context += f"{role}: {msg['content']}\n"
        context += f"пользователь: {message}\nассистент: "

        agent = create_polish_agent()
        result = agent.run(context)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": result})

        # Автосохранение (заголовок из первого сообщения пользователя)
        title = history[0]["content"][:50] if history else "новый диалог"
        polish_sessions.save(session_id, history, title)
        logger.add("Редактура (диалог)", "многораундовая редактура", message, result)
        return "", history, session_id, _polish_sessions_dropdown()
    except Exception as e:
        err = f"Ошибка редактуры: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": err})
        return "", history, session_id, _polish_sessions_dropdown()




def outline_chat(message, history, session_id):
    """Диалог генерации плана — многоходовый, автосохранение сессии"""
    if not message.strip():
        return "", history, session_id, _outline_sessions_dropdown()
    if not session_id:
        session_id = f"outline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        context = ""
        for msg in history:
            role = "пользователь" if msg["role"] == "user" else "ассистент"
            context += f"{role}: {msg['content']}\n"
        context += f"пользователь: {message}\nассистент: "
        agent = create_outline_agent()
        result = agent.run(context)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": result})
        title = history[0]["content"][:50] if history else "новый диалог"
        outline_sessions.save(session_id, history, title)
        logger.add("План (диалог)", "многораундовая корректировка плана", message, result)
        return "", history, session_id, _outline_sessions_dropdown()
    except Exception as e:
        err = f"ошибка генерации: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": err})
        return "", history, session_id, _outline_sessions_dropdown()


def _polish_choices():
    sessions = polish_sessions.list_sessions()
    return [(f"{t} ({u})", sid) for sid, t, u in sessions]

def _outline_choices():
    sessions = outline_sessions.list_sessions()
    return [(f"{t} ({u})", sid) for sid, t, u in sessions]

def _paper_choices():
    sessions = paper_sessions.list_sessions()
    return [(f"{t} ({u})", sid) for sid, t, u in sessions]

def _polish_sessions_dropdown():
    """Список сессий редактуры → gr.update"""
    choices = _polish_choices()
    return gr.update(choices=choices, value=None if not choices else choices[0][1])

def _outline_sessions_dropdown():
    """Список сессий плана → gr.update"""
    choices = _outline_choices()
    return gr.update(choices=choices, value=None if not choices else choices[0][1])

def _paper_sessions_dropdown():
    """Список сессий написания → gr.update"""
    choices = _paper_choices()
    return gr.update(choices=choices, value=None if not choices else choices[0][1])

def clear_polish_chat():
    """Сбросить диалог редактуры"""
    return "", [], "", _polish_sessions_dropdown()


def clear_outline_chat():
    """Сбросить диалог плана"""
    return "", [], "", _outline_sessions_dropdown()


def load_polish_session(session_id):
    """Загрузить историю сессии редактуры в chatbot"""
    if not session_id:
        return [], session_id, _polish_sessions_dropdown()
    try:
        messages = polish_sessions.load(session_id)
        return messages, session_id, _polish_sessions_dropdown()
    except Exception:
        return [], "", _polish_sessions_dropdown()


def load_outline_session(session_id):
    """Загрузить историю сессии плана в chatbot"""
    if not session_id:
        return [], session_id, _outline_sessions_dropdown()
    try:
        messages = outline_sessions.load(session_id)
        return messages, session_id, _outline_sessions_dropdown()
    except Exception:
        return [], "", _outline_sessions_dropdown()

def delete_polish_session(session_id):
    """Удалить историю сессии редактуры"""
    if session_id:
        polish_sessions.delete(session_id)
    return [], "", _polish_sessions_dropdown()

def delete_outline_session(session_id):
    """Удалить историю сессии плана"""
    if session_id:
        outline_sessions.delete(session_id)
    return [], "", _outline_sessions_dropdown()


# ========================================
# Callback написания статьи (диалог)

def paper_write_chat(message, history, session_id):
    """Диалог написания — многораундовый, автосохранение"""
    if not message.strip():
        return "", history, session_id, _paper_sessions_dropdown()
    if not session_id:
        session_id = f"paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        context = ""
        for msg in history:
            role = "пользователь" if msg["role"] == "user" else "ассистент"
            context += f"{role}: {msg['content']}\n"
        context += f"пользователь: {message}\nассистент: "
        agent = create_paper_writer_agent()
        result = agent.run(context)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": result})
        title = history[0]["content"][:50] if history else "новый диалог"
        paper_sessions.save(session_id, history, title)
        logger.add("Написание (диалог)", "многораундовое написание", message, result)
        return "", history, session_id, _paper_sessions_dropdown()
    except Exception as e:
        err = f"Ошибка написания: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": err})
        return "", history, session_id, _paper_sessions_dropdown()

def load_paper_session(session_id):
    """Загрузить историю сессии написания"""
    if not session_id:
        return [], session_id, _paper_sessions_dropdown()
    try:
        messages = paper_sessions.load(session_id)
        return messages, session_id, _paper_sessions_dropdown()
    except Exception:
        return [], "", _paper_sessions_dropdown()

def delete_paper_session(session_id):
    """Удалить историю сессии написания"""
    if session_id:
        paper_sessions.delete(session_id)
    return [], "", _paper_sessions_dropdown()

def clear_paper_chat():
    """Сбросить диалог написания"""
    return "", [], "", _paper_sessions_dropdown()

def extract_pdf(pdf_file, max_chars):
    """Извлечение текста из PDF"""
    if pdf_file is None:
        return "Загрузите PDF-файл."
    try:
        resp = tool_registry.execute_tool("pdf_extract", json.dumps({
            "file_path": pdf_file.name,
            "max_chars": int(max_chars)
        }))
        logger.add("Извлечение PDF", "Извлечение текста из PDF", f"файл: {pdf_file.name}", resp.text)
        return resp.text
    except Exception as e:
        err = f"Ошибка извлечения: {str(e)}"
        logger.add("Извлечение PDF", "ошибка извлечения", f"файл: {pdf_file.name}", err)
        return err


def refresh_history():
    """Обновить отображение журнала диалогов"""
    return logger.format_history_html()


def delete_history_record(record_id):
    """Удалить запись по номеру (кнопка HTML)"""
    if not record_id:
        return logger.format_history_html()
    try:
        rid = int(record_id)
        logger.delete_record(rid)
        return logger.format_history_html()
    except (ValueError, TypeError):
        return logger.format_history_html()


def clear_history():
    """Очистить журнал диалогов"""
    msg = logger.clear()
    return msg


# ========================================
# Разметка Gradio UI
# ========================================

THEME = gr.themes.Soft(primary_hue="blue", secondary_hue="slate")

with gr.Blocks(title="PaperAssistant — умный помощник по статьям") as demo:
    gr.Markdown("""
    # 🎓 PaperAssistant — умный помощник по статьям
    ### Мультиагентный академический инструмент на HelloAgents + DeepSeek
    """)

    with gr.Tab("📚 Поиск литературы"):
        with gr.Row():
            with gr.Column(scale=3):
                search_input = gr.Textbox(
                    label="Тема исследования",
                    placeholder="Ключевые слова на любом языке, напр.: влияние климата на сельское хозяйство...",
                    lines=2
                )
                with gr.Row():
                    search_source = gr.Dropdown(
                        choices=[
                            "Semantic Scholar (все дисциплины)",
                            "AMiner (китайские публикации)",
                            "OpenAlex (открытый доступ)",
                            "PubMed (биомедицина)",
                            "CrossRef (журналы)",
                            "arXiv (CS/математика/физика)"
                        ],
                        value="Semantic Scholar (все дисциплины)",
                        label="Источник данных"
                    )
                    max_results = gr.Slider(1, 10, value=5, step=1, label="Число статей")

                with gr.Accordion("Расширенные фильтры", open=False):
                    search_field = gr.Dropdown(
                        choices=["Все области"] + [
                            "Информатика", "ИИ", "Медицина", "Биология", "Физика", "Химия",
                            "Математика", "Экономика", "Психология", "Социология", "Лингвистика", "Философия",
                            "Инженерия", "Экология", "Материаловедение", "Педагогика", "Право", "Бизнес"
                        ],
                        value="Все области",
                        label="Область"
                    )
                    with gr.Row():
                        year_from = gr.Textbox(label="Год от", placeholder="2020", scale=1)
                        year_to = gr.Textbox(label="Год до", placeholder="2025", scale=1)

                search_btn = gr.Button("🔍 Начать поиск", variant="primary")
            with gr.Column(scale=7):
                search_output = gr.Markdown(label="результаты поиска", value="*Ожидание поиска...*")
        search_btn.click(
            fn=search_papers,
            inputs=[search_input, search_source, max_results, search_field, year_from, year_to],
            outputs=search_output
        )

    with gr.Tab("📝 Резюме статьи"):
        with gr.Row():
            with gr.Column(scale=4):
                summary_input = gr.Textbox(
                    label="Содержание статьи (заголовок, авторы, аннотация)",
                    placeholder="Вставьте информацию о статье: заголовок, авторы, аннотация, методы...",
                    lines=15
                )
                summary_btn = gr.Button("📝 Сгенерировать резюме", variant="primary")
            with gr.Column(scale=6):
                summary_output = gr.Markdown(label="Отчёт-резюме", value="*Ожидание ввода...*")
        summary_btn.click(
            fn=summarize_paper,
            inputs=[summary_input],
            outputs=summary_output
        )

    with gr.Tab("📎 Генерация цитаты"):
        with gr.Row():
            with gr.Column(scale=4):
                cite_title = gr.Textbox(label="Название статьи *", placeholder="Attention Is All You Need")
                cite_authors = gr.Textbox(label="Авторы *", placeholder="Vaswani, A., Shazeer, N., Parmar, N., et al.")
                with gr.Row():
                    cite_journal = gr.Textbox(label="Журнал/конференция", placeholder="NeurIPS")
                    cite_year = gr.Textbox(label="Год", placeholder="2017")
                with gr.Row():
                    cite_volume = gr.Textbox(label="Том", placeholder="30")
                    cite_pages = gr.Textbox(label="Страницы", placeholder="5998-6008")
                cite_doi = gr.Textbox(label="DOI (необязательно)")
                cite_format = gr.Radio(
                    choices=["gbt7714", "apa", "mla"],
                    value="gbt7714",
                    label="Формат цитирования"
                )
                cite_btn = gr.Button("📎 Сгенерировать цитату", variant="primary")
            with gr.Column(scale=6):
                cite_output = gr.Textbox(label="Сгенерированная цитата", lines=8)
        cite_btn.click(
            fn=generate_citation,
            inputs=[cite_title, cite_authors, cite_journal, cite_year,
                    cite_volume, cite_pages, cite_doi, cite_format],
            outputs=cite_output
        )

    with gr.Tab("✍️ Редактура статьи"):
        polish_session_id = gr.State(value="")

        with gr.Accordion("📋 История сессий", open=False):
            with gr.Row():
                polish_history_list = gr.Dropdown(
                    label="История диалогов", choices=_polish_choices(), scale=6,
                    info="Выберите сессию и нажмите «Загрузить» для продолжения"
                )
                polish_load_btn = gr.Button("📂 Загрузить", variant="primary", size="sm", scale=1)
                polish_del_btn = gr.Button("🗑️ Удалить", variant="stop", size="sm", scale=1)

        gr.Markdown("Вставьте текст и продолжайте диалог: «сделай формальнее», «сократи третий абзац» — контекст сохраняется.")
        polish_chatbot = gr.Chatbot(label="Диалог редактуры", height=450)
        with gr.Row():
            polish_msg = gr.Textbox(
                label="Запрос на правку",
                placeholder="Например: отредактируйте этот фрагмент... / сделайте второй абзац более академичным...",
                scale=7
            )
            polish_send = gr.Button("Отправить", variant="primary", scale=1)
        polish_clear = gr.Button("🗑️ Новый диалог", size="sm", variant="stop")

        # Привязка событий
        polish_send.click(
            fn=polish_chat,
            inputs=[polish_msg, polish_chatbot, polish_session_id],
            outputs=[polish_msg, polish_chatbot, polish_session_id, polish_history_list]
        )
        polish_msg.submit(
            fn=polish_chat,
            inputs=[polish_msg, polish_chatbot, polish_session_id],
            outputs=[polish_msg, polish_chatbot, polish_session_id, polish_history_list]
        )
        polish_clear.click(
            fn=clear_polish_chat,
            outputs=[polish_msg, polish_chatbot, polish_session_id, polish_history_list]
        )
        polish_load_btn.click(
            fn=load_polish_session,
            inputs=[polish_history_list],
            outputs=[polish_chatbot, polish_session_id, polish_history_list]
        )
        polish_del_btn.click(
            fn=delete_polish_session,
            inputs=[polish_history_list],
            outputs=[polish_chatbot, polish_session_id, polish_history_list]
        )

    with gr.Tab("📊 Генерация плана"):
        outline_session_id = gr.State(value="")

        with gr.Accordion("📋 История сессий", open=False):
            with gr.Row():
                outline_history_list = gr.Dropdown(
                    label="История диалогов", choices=_outline_choices(), scale=6,
                    info="Выберите сессию и нажмите «Загрузить» для продолжения"
                )
                outline_load_btn = gr.Button("📂 Загрузить", variant="primary", size="sm", scale=1)
                outline_del_btn = gr.Button("🗑️ Удалить", variant="stop", size="sm", scale=1)

        gr.Markdown("Введите тему и уточняйте план в диалоге: «детализируй главу 3», «добавь раздел сравнения экспериментов».")
        outline_chatbot = gr.Chatbot(label="Диалог по плану", height=450)
        with gr.Row():
            outline_msg = gr.Textbox(
                label="Запрос",
                placeholder="Например: нужен план диплома по теме XX...",
                scale=7
            )
            outline_send = gr.Button("Отправить", variant="primary", scale=1)
        outline_clear = gr.Button("🗑️ Новый диалог", size="sm", variant="stop")

        # Привязка событий
        outline_send.click(
            fn=outline_chat,
            inputs=[outline_msg, outline_chatbot, outline_session_id],
            outputs=[outline_msg, outline_chatbot, outline_session_id, outline_history_list]
        )
        outline_msg.submit(
            fn=outline_chat,
            inputs=[outline_msg, outline_chatbot, outline_session_id],
            outputs=[outline_msg, outline_chatbot, outline_session_id, outline_history_list]
        )
        outline_clear.click(
            fn=clear_outline_chat,
            outputs=[outline_msg, outline_chatbot, outline_session_id, outline_history_list]
        )
        outline_load_btn.click(
            fn=load_outline_session,
            inputs=[outline_history_list],
            outputs=[outline_chatbot, outline_session_id, outline_history_list]
        )
        outline_del_btn.click(
            fn=delete_outline_session,
            inputs=[outline_history_list],
            outputs=[outline_chatbot, outline_session_id, outline_history_list]
        )

    with gr.Tab("📝 Написание статьи"):
        paper_session_id = gr.State(value="")

        with gr.Accordion("📋 История сессий", open=False):
            with gr.Row():
                paper_history_list = gr.Dropdown(
                    label="История диалогов", choices=_paper_choices(), scale=6,
                    info="Выберите сессию для продолжения написания"
                )
                paper_load_btn = gr.Button("📂 Загрузить", variant="primary", size="sm", scale=1)
                paper_del_btn = gr.Button("🗑️ Удалить", variant="stop", size="sm", scale=1)

        gr.Markdown("Пишите по плану главу за главой. Вставьте план и скажите «начни с первой главы» — можно править в диалоге.")
        paper_chatbot = gr.Chatbot(label="Диалог написания", height=450)
        with gr.Row():
            paper_msg = gr.Textbox(
                label="Запрос на написание",
                placeholder="Например: вот план... начни с аннотации / напиши главу 3 / добавь деталей...",
                scale=7
            )
            paper_send = gr.Button("Отправить", variant="primary", scale=1)
        with gr.Row():
            paper_clear = gr.Button("🗑️ Новый диалог", size="sm", variant="stop")

        paper_send.click(
            fn=paper_write_chat,
            inputs=[paper_msg, paper_chatbot, paper_session_id],
            outputs=[paper_msg, paper_chatbot, paper_session_id, paper_history_list]
        )
        paper_msg.submit(
            fn=paper_write_chat,
            inputs=[paper_msg, paper_chatbot, paper_session_id],
            outputs=[paper_msg, paper_chatbot, paper_session_id, paper_history_list]
        )
        paper_clear.click(
            fn=clear_paper_chat,
            outputs=[paper_msg, paper_chatbot, paper_session_id, paper_history_list]
        )
        paper_load_btn.click(
            fn=load_paper_session,
            inputs=[paper_history_list],
            outputs=[paper_chatbot, paper_session_id, paper_history_list]
        )
        paper_del_btn.click(
            fn=delete_paper_session,
            inputs=[paper_history_list],
            outputs=[paper_chatbot, paper_session_id, paper_history_list]
        )
    with gr.Tab("📄 PDF → Markdown"):
        gr.Markdown("Загрузите PDF — система распознает заголовки, главы и абзацы и вернёт **Markdown**.")
        with gr.Row():
            with gr.Column(scale=4):
                pdf_input = gr.File(label="Загрузить PDF", file_types=[".pdf"])
                pdf_max_chars = gr.Slider(0, 100000, value=0, step=1000,
                                           label="Лимит символов (0 = без лимита)")
                pdf_btn = gr.Button("📄 Конвертировать в Markdown", variant="primary")
            with gr.Column(scale=6):
                pdf_output = gr.Code(label="Вывод Markdown", language="markdown", lines=20)
        pdf_btn.click(
            fn=extract_pdf,
            inputs=[pdf_input, pdf_max_chars],
            outputs=pdf_output
        )

    with gr.Tab("💬 История диалогов"):
        with gr.Row():
            refresh_btn = gr.Button("🔄 Обновить", size="sm")
            clear_btn = gr.Button("🗑️ Очистить всё", size="sm", variant="stop")

        # Скрытый триггер: кнопка удаления через JS
        delete_trigger = gr.Textbox(visible=False, elem_id="del_trigger")

        # Отображение истории (HTML, кнопка удаления)
        history_display = gr.HTML(value=logger.format_history_html())

        refresh_btn.click(fn=refresh_history, outputs=history_display)
        clear_btn.click(fn=clear_history, outputs=history_display)
        delete_trigger.change(
            fn=delete_history_record,
            inputs=[delete_trigger],
            outputs=[history_display]
        )

    gr.Markdown("""
    ---
    ### 👤 Автор: [@chengH425](https://github.com/chengH425) | 🙏 Спасибо сообществу Datawhale и проекту Hello-Agents
    """)


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, theme=THEME)
