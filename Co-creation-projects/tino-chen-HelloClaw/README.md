# HelloClaw — персональный AI Agent-ассистент

> Персональное AI Agent-приложение на HelloAgents: настройка личности, память и потоковый вызов инструментов

<div align="center">
  <img src="outputs/helloclaw.png" alt="HelloClaw Screenshot" width="80%"/>
</div>

## О проекте

HelloClaw — персональное AI Agent-приложение на фреймворке Hello-Agents с функциями в духе OpenClaw. Это не только чат-ассистент, но и партнёр, который «знает» вас, запоминает контекст и растёт вместе с вашими задачами.

**Ключевые возможности:**
- Настраиваемая личность и идентичность агента
- Долгая и ежедневная память с автоматическим управлением
- Потоковый вызов инструментов с отображением статуса в реальном времени
- Несколько сессий, персистентная история
- Современный веб-интерфейс (Vue3 + FastAPI)

## Основные функции

- [x] **Умный диалог** — ReActAgent
- [x] **Память** — долгая (`MEMORY.md`) и ежедневная
- [x] **Инструменты** — файлы, выполнение кода, поиск, парсинг страниц и др.
- [x] **Сессии** — несколько чатов, сохранение истории
- [x] **Идентичность** — конфигурация личности агента
- [x] **Потоковый вывод** — SSE в реальном времени
- [x] **Веб-интерфейс** — Vue3

## Стек

| Уровень | Технологии |
|------|------|
| Agent | Hello-Agents (ReActAgent / SimpleAgent) |
| Бэкенд | Python + FastAPI |
| Фронтенд | Vue 3 + TypeScript + Ant Design Vue |
| Поток | SSE (Server-Sent Events) |
| Пакеты | uv (Python) / pnpm (фронтенд) |

## Технические особенности

### 1. Расширенный потоковый вызов инструментов

`EnhancedSimpleAgent` и `EnhancedHelloAgentsLLM` — настоящий потоковый tool calling:
- статус вызова в реальном времени (старт/завершение)
- несколько раундов tool calls
- обработка ошибок и откат

### 2. Умная память

- **Долгая (`MEMORY.md`)**: важное между сессиями
- **Ежедневная**: диалоги по датам
- **Memory Flush**: при приближении к лимиту контекста — напоминание сохранить важное

### 3. Рабочее пространство

- Настройка личности через Markdown-конфиги
- `IDENTITY.md`, `USER.md`, `SOUL.md` и др.
- Горячая перезагрузка без рестарта

## Быстрый старт

### Требования

- Python 3.10+
- Node.js 18+ (опционально, только для фронтенда)

### Установка

```bash
pip install -r requirements.txt
```

### API-ключ

```bash
# Создать .env
cp .env.example .env

# Указать ключ в .env
# Поддерживаются OpenAI-совместимые API (Zhipu AI, ModelScope и др.)
```

### Запуск

**Вариант 1: Jupyter Notebook (рекомендуется)**

```bash
jupyter lab
# Откройте main.ipynb и выполните ячейки
```

**Вариант 2: полный веб-сервис**

```bash
# Бэкенд
cd tino-chen-HelloClaw
pip install uvicorn
uvicorn src.main:app --reload --port 8000

# Фронтенд (новый терминал)
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173

## Примеры

### Базовый диалог

```python
from src.agent.helloclaw_agent import HelloClawAgent

# Создать Agent
agent = HelloClawAgent()

# Синхронный чат
response = agent.chat("Привет, расскажи о себе")
print(response)
```

### Потоковый диалог

```python
import asyncio

async def chat_stream():
    agent = HelloClawAgent()

    async for event in agent.achat("Найди новости за сегодня"):
        if event.type.value == "llm_chunk":
            print(event.data.get("chunk", ""), end="", flush=True)
        elif event.type.value == "tool_call_start":
            print(f"\n[Вызов инструмента: {event.data.get('tool_name')}]")
        elif event.type.value == "tool_call_finish":
            print(f"[Инструмент завершён]")

asyncio.run(chat_stream())
```

## Структура проекта

```
tino-chen-HelloClaw/
├── README.md              # Документация
├── requirements.txt       # Python-зависимости
├── main.ipynb            # Jupyter Notebook (быстрая демо)
├── .env.example          # Шаблон переменных окружения
├── data/                 # Данные
├── outputs/              # Результаты (скриншоты и т.д.)
│   └── helloclaw.png     # Скриншот проекта
├── src/                  # Бэкенд
│   ├── agent/            # Обёртки Agent
│   │   ├── helloclaw_agent.py      # Главный класс Agent
│   │   ├── enhanced_simple_agent.py # Расширенный SimpleAgent
│   │   └── enhanced_llm.py         # Расширенный LLM (потоковые tools)
│   ├── tools/            # Свои инструменты
│   │   └── builtin/
│   │       ├── memory.py              # Память
│   │       ├── execute_command.py     # Выполнение команд
│   │       ├── web_search.py          # Поиск в веб
│   │       └── web_fetch.py           # Загрузка страниц
│   ├── memory/           # Управление памятью
│   │   ├── capture.py             # Захват памяти
│   │   ├── memory_flush.py        # Сброс памяти в хранилище
│   │   └── session_summarizer.py  # Сводка сессии
│   ├── workspace/        # Рабочее пространство
│   │   ├── manager.py             # Менеджер workspace
│   │   └── templates/             # Шаблоны конфигов
│   └── api/              # Маршруты FastAPI
│       ├── chat.py                # Чат
│       ├── session.py             # Сессии
│       ├── config.py              # Конфигурация
│       └── memory.py              # API памяти
└── frontend/             # Vue3
    ├── src/
    │   ├── views/                 # Страницы
    │   ├── components/            # Компоненты
    │   ├── api/                   # HTTP-клиент
    │   └── assets/                # Статика
    ├── public/
    ├── package.json
    └── vite.config.ts
```

## Конфигурация workspace

Каталог `~/.helloclaw/`:

```
~/.helloclaw/
├── config.json       # Глобальная конфигурация LLM
└── workspace/        # Workspace агента
    ├── IDENTITY.md   # Идентичность
    ├── MEMORY.md     # Долгая память
    ├── SOUL.md       # Характер / «душа»
    ├── USER.md       # Данные пользователя
    ├── AGENTS.md     # Системный промпт
    ├── memory/       # Ежедневная память
    └── sessions/     # История сессий
```

## Сильные стороны

1. **Настоящий потоковый tool calling** — не только текст, а полный цикл вызова инструментов
2. **Умная память** — важное из диалогов, долгая и ежедневная память
3. **Гибкая настройка** — личность, характер, профиль пользователя через Markdown
4. **Продакшен-уровень** — ошибки, логи, конфигурация

## Планы

- [ ] Мультимодальный ввод (изображения, файлы)
- [ ] Больше встроенных tools (интерпретатор, БД и т.д.)
- [ ] Совместная работа нескольких агентов
- [ ] Голосовое взаимодействие

## Лицензия

MIT License

## Автор

- GitHub: [@tino-chen](https://github.com/tino-chen)
- Проект: [HelloClaw](https://github.com/tino-chen/helloclaw)

## Благодарности

- [Hello-Agents](https://github.com/datawhalechina/hello-agents) — фреймворк агентов
- [FastAPI](https://fastapi.tiangolo.com/) — бэкенд
- [Vue.js](https://vuejs.org/) — фронтенд
- [Ant Design Vue](https://antdv.com/) — UI

Спасибо сообществу Datawhale и проекту Hello-Agents!
