# HealthRecordAgent · Помощник по медицинским записям

Многоагентное приложение на **HelloAgents** (`HelloAgentsLLM`) и **FastAPI**: расшифровка медосмотров, рекомендации по питанию и цикл обратной связи; опционально **семантический поиск Milvus + SQLite** для долгой памяти.

> **Дисклеймер**: вывод проекта — только демонстрация здоровья и процессов, **не заменяет** диагноз или назначения врача.

---

## Обзор интерфейса

Скриншоты в **`frontend/screenshots/`** — при обновлении заменяйте файлы с теми же именами.

**Записи и отчёты** (`report.png`)

![Записи и отчёты](frontend/screenshots/report.png)

**Рекомендации по питанию** (`diet.png`)

![Рекомендации по питанию](frontend/screenshots/diet.png)

**Обратная связь Reflect** (`reflect.png`)

![Обратная связь Reflect](frontend/screenshots/reflect.png)

---

## Обзор функций

| Модуль | Описание |
|------|------|
| **Анализ записей** | Текст или PDF медотчёта → конвейер агентов (план → показатели → риски → рекомендации → отчёт), асинхронные задачи с опросом статуса |
| **Помощник по питанию** | **Дневник питания** на естественном языке → разбор LLM и сводка нутриентов → многоэтапный вывод (нутрициолог / тренер / привычки); история памяти и Reflect |
| **Долгая память** | SQLite для запусков и обратной связи; опционально Milvus + гибридный поиск (при сбое — список из SQL) |
| **Наблюдаемость** | `pipeline_trace`, `errors` / `degraded`, `rag_debug`; observability для отчётов/питания и **replay** питания |
| **Фронтенд** | Статика + вкладки (анализ \| питание \| история); иерархия в духе Apple Health; **режим разработчика** для технических деталей; цикл **Reflect** по питанию |

---

## Архитектура

- **Оркестрация**: анализ здоровья в стиле **Plan-and-Execute** (`PlannerAgent`, затем специалисты); питание — **многоэтапный конвейер** (разбор еды → нутрициолог → тренер → привычки) с **Pydantic** и деградацией при ошибках.
- **Инструменты**: **Tool Use** в сценарии питания (запрос нутриентов, mock активности/сна — можно заменить реальными источниками).
- **LLM**: `hello_agents.HelloAgentsLLM`, OpenAI-совместимый API; базовые классы и пайплайны в `backend/agents`, `backend/service`.
- **Память и RAG**: отчёты, питание и feedback в **SQLite**; при семантическом поиске — **векторный индекс (Milvus)** по пользователю и сценарию. Без Milvus — **автооткат** на недавние записи из SQL.

---

## Структура (фрагмент)

```
HealthRecordAgent/
├── README.md
├── requirements.txt
├── data/                    # SQLite по умолчанию: health_memory.db (можно в .gitignore)
├── backend/
│   ├── api/main.py          # Точка входа FastAPI
│   ├── agents/              # Агенты анализа отчётов
│   ├── service/             # health_analysis, diet_pipeline и др.
│   ├── memory/              # Доступ к SQLite
│   ├── rag/                 # Эмбеддинги, Milvus, retrieve
│   └── tools/               # Инструменты питания
└── frontend/
    ├── index.html, app.js, style.css
    └── screenshots/         # Скриншоты для README (см. «Обзор интерфейса»)
```

---

## Требования

- **Python**: 3.10+ (рекомендуется venv)
- **Опционально**: локальный **Milvus** (Docker) и **Embedding** API для RAG

---

## Быстрый старт

### 1. Установка зависимостей

В **корне проекта** `HealthRecordAgent` (где этот README):

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate   # Windows: backend\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Переменные окружения

Создайте `.env` в **`backend/`** (`python-dotenv` грузит из рабочей директории; **запускайте Uvicorn из `backend/`**):

```bash
cd backend
cp .env.example .env
# Минимум OPENAI_API_KEY; для шлюза — OPENAI_BASE_URL
```

Подробности в **`backend/.env.example`**. Для семантической памяти: `RAG_ENABLED=true`, доступны `MILVUS_URI` и переменные эмбеддингов.

### 3. Запуск бэкенда

```bash
cd backend
source .venv/bin/activate
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

- Swagger: **http://127.0.0.1:8000/docs**
- Префикс: **`/api`** (например `POST /api/health/analysis`)

### 4. Фронтенд (статика)

В другом терминале:

```bash
cd frontend
python3 -m http.server 8080 --bind 127.0.0.1
```

Браузер: **http://127.0.0.1:8080/**  

По умолчанию запросы на **`http://127.0.0.1:8000`** (`API_BASE` в `frontend/app.js`) — порт должен совпадать с бэкендом.

---

## API

### Анализ здоровья

| Метод | Путь | Описание |
|------|------|------|
| POST | `/api/health/analysis` | Анализ текстового отчёта, возвращает `task_id` |
| POST | `/api/health/analysis/pdf` | Загрузка PDF |
| GET | `/api/health/task_status/{task_id}` | Статус задачи и агентов |
| GET | `/api/health/users/{user_id}/report_history` | История отчётов пользователя |
| GET | `/api/health/report_runs/{task_id}` | Детали одного запуска |
| GET | `/api/health/report_runs/{task_id}/observability` | Сводка наблюдаемости |

### Питание

| Метод | Путь | Описание |
|------|------|------|
| POST | `/api/diet/recommend` | Рекомендации (`context.today_food_log_text` и др.) |
| POST | `/api/diet/reflect` | Выполнение рекомендаций и причины (память цикла) |
| GET | `/api/diet/users/{user_id}/runs` | История запусков питания |
| GET | `/api/diet/users/{user_id}/reflect_history` | История feedback |
| GET | `/api/diet/runs/{run_id}` | Один run питания |
| GET | `/api/diet/runs/{run_id}/observability` | Наблюдаемость |
| POST | `/api/diet/runs/{run_id}/replay` | Повтор с тем же вводом (новый `run_id`) |

---

## Milvus (опционально)

1. Поднимите Milvus (Docker Compose или образ), порт **`19530`** как в `MILVUS_URI`.
2. `RAG_ENABLED=true`, Embedding как в `.env.example`.
3. Для индексации истории — скрипт вроде `backend/scripts/reindex_milvus.py` при наличии.

Без Milvus поиск откатывается на **список из SQL** — основной сценарий демо не ломается.

---

## Частые вопросы

- **Фронт открывается, API падает**: бэкенд на **8000** или тот же порт, что в `frontend/app.js` → `API_BASE`.
- **RAG не работает**: `RAG_ENABLED`, процесс Milvus, Embedding API; в ответе `rag_debug.mode` — `milvus` или откат.
- **Файл БД**: по умолчанию **`HealthRecordAgent/data/health_memory.db`**, переопределение — `HEALTH_MEMORY_DB_PATH`.

---

## Ссылки

- [Hello-Agents — курс и сообщество](https://github.com/datawhalechina/hello-agents)
- Автор: [@Shawnxyxy](https://github.com/Shawnxyxy)

## Благодарности

**DataWhale** и **Hello-Agents** за курс и экосистему `hello-agents`.

---

## Участие и лицензия

Issue и PR приветствуются. Соблюдайте лицензию репозитория и upstream; при цитировании как учебного примера укажите источник.
