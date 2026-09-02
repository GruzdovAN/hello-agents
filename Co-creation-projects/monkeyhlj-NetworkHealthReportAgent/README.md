# NetworkHealthReportAgent

Многоагентная система отчётов о состоянии сети на базе Hello-Agents: карта с площадками, просмотр отчёта по клику, запросы за последнюю неделю и за произвольный период.

## 📝 О проекте

Проект для корпоративной сетевой эксплуатации: демонстрация совместной работы нескольких агентов для генерации понятных и применимых отчётов о здоровье сети.

- Фронтенд (Vue + Leaflet): географическое расположение площадок, отчёт по клику
- Бэкенд (FastAPI): API площадок, отчётов, глобального Q&A, потокового вывода и скачивания отчётов
- Слой агентов (HelloAgents):

1. Агент анализа логов
2. Агент состояния сетевого оборудования
3. Агент анализа состояния пользователей сети
4. Агент отчёта о здоровье сети (сводка результатов первых трёх)
5. Глобальный Q&A-агент (вопросы по площадкам и намерение экспорта отчёта)

- Слой MCP (FastMCP): чтение данных о площадках, устройствах, логах и соответствии терминалов из каталога `data`

## ✨ Основные возможности

- Визуализация площадок на карте, отчёт по клику
- Окно по умолчанию — последние 7 дней
- Произвольные `start_date` и `end_date`
- Тестовые данные: площадки, реестр устройств, временные ряды состояния, сетевые логи, соответствие терминалов
- Глобальный Q&A: например «сколько site?», «какие site в Шанхае?», «как обстоят дела с устройствами на site?», «сгенерируй отчёт по site в Чэнду за неделю»
- Экспорт отчёта из Q&A: файлы `outputs/*.md` и ссылка на скачивание

## 🛠️ Стек

- HelloAgents (hello-agents)
- FastAPI
- FastMCP
- Vue 3 + Vite + Leaflet

## 📂 Структура каталогов

```text
monkeyhlj-NetworkHealthReportAgent/
├── README.md                               # Документация проекта
├── requirements.txt                        # Python-зависимости
├── .env.example                            # Шаблон переменных LLM/модели
├── main.ipynb                              # Notebook (7 частей walkthrough)
├── run_api.py                              # Точка входа FastAPI (uvicorn указывает сюда)
├── data/
│   ├── sites.json                          # Геоданные площадок (широта/долгота, регион, уровень)
│   ├── device_inventory.json               # Реестр устройств (коммутаторы/WLC/AP и т.д.)
│   ├── device_status_timeseries.json       # Временные ряды состояния (доступность, задержка, потери и т.д.)
│   ├── network_logs.json                   # Сетевые логи (события алертов)
│   ├── terminal_compliance.json            # Данные подключения и соответствия терминалов
│   └── test_cases.json                     # Примеры тестов API отчётов
├── outputs/
│   ├── review_report.md                    # Пример отчёта
│   └── site-*_YYYY-MM-DD_*.md             # Еженедельные отчёты по площадкам из Q&A (генерируются)
├── src/
│   ├── __init__.py
│   ├── api/
│   │   └── main.py                         # Маршруты API (/api/sites /api/reports /api/chat /api/chat/stream /api/outputs)
│   ├── agents/
│   │   ├── base.py                         # Базовый класс Agent: LLM и MCPTool
│   │   ├── log_analysis_agent.py           # Агент анализа логов
│   │   ├── device_status_agent.py          # Агент состояния устройств
│   │   ├── user_status_agent.py            # Агент состояния пользователей
│   │   ├── network_health_report_agent.py  # Агент сводного отчёта
│   │   ├── site_qa_agent.py                # Глобальный Q&A / экспорт отчётов
│   │   └── orchestrator.py                 # Оркестрация агентов и общий поток
│   ├── tools/
│   │   ├── data_repository.py              # Слой доступа к данным (чтение data/*.json)
│   │   └── data_mcp_server.py              # MCP-сервер, инструменты данных для агентов
│   └── utils/
│       └── date_utils.py                   # Окно дат (по умолчанию последние 7 дней)
└── frontend/
    ├── package.json                         # Зависимости и скрипты фронтенда
    ├── vite.config.js                       # Конфигурация Vite
    ├── index.html
    └── src/
        ├── main.js                          # Точка входа фронтенда
        ├── App.vue                          # Главный вид (карта слева + отчёт снизу + Q&A справа)
        ├── api.js                           # Вызовы API и определение адреса бэкенда
        ├── styles.css                       # Стили
        └── components/
            ├── SiteMap.vue                  # Компонент карты
            └── ReportPanel.vue              # Панель отчёта
```

Примечание: в дереве опущены `venv/`, `__pycache__/`, `.idea/`, `memory/` и другие каталоги среды выполнения.

## 🤖 Режимы работы

Поддерживаются два режима:

1. Без LLM (можно сразу демонстрировать)

- Работает без `LLM_API_KEY` / `OPENAI_API_KEY`.
- Отчёт строится локальными правилами — удобно для офлайн-демо и отладки.

2. С LLM (рекомендуется)

- Нужен API Key.
- Агенты создают `HelloAgentsLLM` и подключают MCP-инструменты данных (совместимость с разными версиями hello-agents).

## 🔐 Запуск с LLM (важно)

### 1) Переменные окружения

Скопируйте шаблон:

```bash
cp .env.example .env
```

В Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Настройте хотя бы одну из групп:

- Единая конфигурация (рекомендуется)

```env
LLM_MODEL_ID=gpt-4o-mini
LLM_API_KEY=ваш_ключ
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT=60
```

- OpenAI-совместимая конфигурация (альтернатива)

```env
OPENAI_API_KEY=ваш_ключ
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

В `agents/base.py` LLM включается так:

- читается `LLM_API_KEY` или `OPENAI_API_KEY`
- при наличии ключа создаётся `HelloAgentsLLM`
- без ключа — режим без LLM

### 2) Запуск бэкенда

```bash
uvicorn run_api:app --reload --port 8000
```

### 3) Проверка LLM

- Health check:

```bash
curl "http://localhost:8000/api/health"
```

- Запрос отчёта по любой площадке:

```bash
curl "http://localhost:8000/api/reports/site-sh-fin"
```

## 🚀 Быстрый старт

### 1) Python и зависимости

```bash
pip install -r requirements.txt
```

### 2) Переменные окружения

```bash
cp .env.example .env
```

В Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Для режима с LLM укажите в `.env` `LLM_API_KEY` (или `OPENAI_API_KEY`).

### 3) Запуск API

```bash
uvicorn run_api:app --reload --port 8000
```

API: `http://localhost:8000`

- Список площадок: `GET /api/sites`
- Отчёт по площадке: `GET /api/reports/{site_id}`
- Параметры: `start_date`, `end_date` (формат `YYYY-MM-DD`)
- Отчёты по всем площадкам: `GET /api/reports`
- Q&A: `POST /api/chat`
- Потоковый Q&A: `POST /api/chat/stream`
- Скачивание отчёта: `GET /api/outputs/{filename}`
- Состояние runtime: `GET /api/runtime`

### 4) Запуск фронтенда

```bash
cd frontend
npm install
npm run dev
```

Фронтенд по умолчанию: `http://localhost:5173`

## 📖 Примеры

Отчёт по площадке в Шанхае за последнюю неделю:

```bash
curl "http://localhost:8000/api/reports/site-sh-fin"
```

Произвольное окно для площадки в Шэньчжэне:

```bash
curl "http://localhost:8000/api/reports/site-sz-ops?start_date=2026-05-23&end_date=2026-05-29"
```

Отчёты по всем площадкам:

```bash
curl "http://localhost:8000/api/reports"
```

Q&A-агент: отчёт за неделю и ссылка на файл:

```bash
curl -X POST "http://localhost:8000/api/chat" \
	-H "Content-Type: application/json" \
	-d '{
		"question": "Сгенерируй отчёт по site-sh-fin за последнюю неделю",
		"site_id": "site-sh-fin",
		"start_date": "2026-05-23",
		"end_date": "2026-05-29"
	}'
```

В ответе будет `artifact.download_url` — ссылка на скачивание; файлы по умолчанию в `outputs/`.

Глобальный Q&A:

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
	-H "Content-Type: application/json" \
	-d '{
		"question": "Какие site есть в Шанхае?",
		"start_date": "2026-05-23",
		"end_date": "2026-05-29"
	}'
```

При выбранной площадке фраза «сгенерируй отчёт по текущей площадке за неделю» тоже запускает экспорт.

## 🧪 Notebook

```bash
jupyter lab
```

Откройте `main.ipynb`:

- Часть 1: введение
- Часть 2: настройка окружения
- Часть 3: инструменты (`SiteQuickLookupTool`)
- Часть 4: агенты (`NetworkHealthOrchestrator` + опционально `demo_agent`)
- Часть 5: демо (Q&A, отчёты, ссылки на скачивание)
- Часть 6: оценка производительности (опционально)
- Часть 7: итоги и планы

## 🎯 Сильные стороны

- Прослеживаемость от данных до агентов: у каждого вывода есть исходные метрики
- MCP абстрагирует доступ к данным — легко подключить реальные источники
- Разделение фронтенда и бэкенда — проще расширять алертинг, тикеты и дашборды

## 🔮 Дальнейшие шаги

- Реальные источники (SNMP/Telemetry/NetFlow)
- Хранилище временных рядов и прогнозирование
- Экспорт отчётов (PDF/Markdown) и автоотправка (почта/ Feishu)

## 🧰 Частые вопросы

1. Ошибка `cannot import name MCPTool`

- Причина: в разных версиях hello-agents разные пути экспорта.
- Сейчас: в `base.py` есть совместимость; при отсутствии модуля — откат, система работает.

2. API отвечает, но не в стиле LLM

- Причина: не заданы `LLM_API_KEY`/`OPENAI_API_KEY`, режим без LLM.
- Решение: заполните `.env` и перезапустите uvicorn.

3. Q&A работает, но экспорт еженедельного отчёта площадки падает

- Причина: для экспорта нужен LLM; без него или при сбое вызова — подсказка без файла.
- Решение: проверьте `LLM_API_KEY` (или `OPENAI_API_KEY`) и доступность модели.

4. Ошибки фронтенда (CORS или соединение)

- Бэкенд на порту 8000.
- Фронтенд на порту 5173.

5. Нужно ли отдельно запускать MCP Server

- Обычно нет: `MCPTool(server_command=[...])` поднимает сервис при вызове агента.
- Вручную — только для отладки MCP:

```bash
python -m src.tools.data_mcp_server
```

## 📄 Лицензия

MIT License

## 🙏 Благодарности

Спасибо сообществу Datawhale и проекту Hello-Agents!
