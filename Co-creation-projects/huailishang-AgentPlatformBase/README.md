# AgentPlatformBase — платформа задач с двумя агентами

`AgentPlatformBase` — лёгкая платформа агентов для выпускного проекта Hello-Agents, глава 16. FastAPI даёт единый бэкенд, браузерный фронтенд — точку входа для диалога; подключены два агента с понятной бизнес-ценностью: поисковик `deep_research` и агент новостей `rss_digest`.

## Основные возможности

- Единый реестр агентов: бэкенд управляет разными агентами через `AgentRegistry`.
- Фоновое выполнение задач: длительные задачи по умолчанию идут в фоне, фронтенд опрашивает статус и не блокирует поле ввода.
- Поисковик: встроенный DeepResearchAgent, формирует отчёты по исследованиям, сохраняет артефакты запуска и долгосрочные заметки.
- Агент новостей: загружает RSS, извлекает основной текст, вызывает LLM для краткого изложения на китайском и рендерит HTML-дайджест.
- Разделение данных: все данные агентов лежат в `data/{agent_id}/` — удобно чистить и исключать из коммита.

## Структура проекта

```text
agent_platform_base/
  backend/
    agents/
      adapters/
        deep_research.py
        rss_digest.py
      base.py
      profiles.py
      registry.py
    memory/
    tasks/
    main.py
    config.py
    maintenance.py
    events.py
    models.py

  frontend/
    index.html
    styles.css
    app.js

  agents/
    deep_research/
      README.md
      src/
        agent.py
        config.py
        services/
    rss_digest/
      src/rss_digest/
      config/
      scripts/
      main.py
      README.md

  data/
    deep_research/
      runs/
      notes/
    rss_digest/
      runs/
      state/

  .env.example
  requirements.txt
  smoke_test.py
```

Правила каталогов:

- `backend/` — бэкенд платформы: только API, задачи, реестр, адаптеры и общая логика.
- `frontend/` — одностраничное рабочее место.
- `agents/{agent_id}/` — код, конфигурация и скрипты конкретного агента.
- `data/{agent_id}/runs/` — артефакты запусков, которые можно удалять.
- `data/{agent_id}/notes/` — долгосрочные знания и заметки; создаётся только у нужных агентов.
- `data/{agent_id}/state/` — персистентное состояние, например база дедупликации RSS.

## Стек технологий

- Python 3.10+
- FastAPI / Uvicorn
- Pydantic
- hello-agents / OpenAI SDK / Tavily / DDGS
- Requests / стандартная библиотека Python для RSS и разбора HTML
- Нативные HTML, CSS, JavaScript

## Быстрый старт

```powershell
cd Co-creation-projects\huailishang-AgentPlatformBase
python -m pip install -r requirements.txt
python main.py
```

Открыть:

- Рабочее место фронтенда: http://127.0.0.1:8016/app/
- Документация API: http://127.0.0.1:8016/docs
- Проверка здоровья: http://127.0.0.1:8016/health

## Примеры использования

В поле ввода фронтенда нужно указать агента через `@`:

```text
@deep_research Исследование архитектуры платформ AI Agent
@rss_digest Сводка за сегодня
@rss_digest Принудительно обновить сводку за сегодня
```

Если HTML-дайджест RSS за сегодня уже создан, обычный `@rss_digest Сводка за сегодня` вернёт существующий дайджест без повторной загрузки и повторного расхода LLM. При вводе «принудительно», «пересоздать», «обновить» или `force/refresh` pipeline RSS запускается заново.

## Механизм работы

```text
POST /tasks
POST /tasks/{task_id}/run        фоновый запуск по умолчанию, сразу возвращает running
GET  /tasks/{task_id}            фронтенд опрашивает до completed / failed
```

Для синхронной отладки:

```text
POST /tasks/{task_id}/run?background=false
```

После завершения задачи в `artifacts.elapsed_seconds` записывается общее время. У RSS и DeepResearch также фиксируется детализация по этапам — для последующей оптимизации.

## Конфигурация RSS по умолчанию

```env
RSS_SOURCE_LIMIT=10
RSS_ENTRIES_PER_SOURCE=5
RSS_MAX_NEW_ARTICLES_PER_RUN=50
RSS_MAX_SUMMARY_ARTICLES_PER_RUN=10
RSS_AI_MAX_CONCURRENCY=2
RSS_RELEVANCE_THRESHOLD=65
RSS_MAX_DIGEST_ARTICLES=12
```

В логах бэкенда RSS остаются только этапы и итоговая статистика; построчные логи по feed, статьям и сводкам в бэкенд не пишутся.

## Политика очистки

Логика очистки в `backend/maintenance.py`, при длительных вызовах срабатывает лениво:

- `RESEARCH_RUN_RETENTION_DAYS=7` — удаляет артефакты запусков поисковика старше 7 дней.
- `RSS_DIGEST_RETENTION_DAYS=7` — удаляет HTML-дайджесты RSS старше 7 дней.
- `RSS_CACHE_RETENTION_DAYS=7` — удаляет сырой HTML RSS, извлечённый текст и кэш перевода старше 7 дней.
- `data/deep_research/notes` автоматически не удаляется.
- `data/rss_digest/state/articles.json` автоматически не удаляется.

## Самопроверка

```powershell
cd Co-creation-projects\huailishang-AgentPlatformBase
python smoke_test.py
```

При успехе вывод:

```text
chapter16 platform smoke test passed
```

## Примечания к сдаче

По требованиям главы 16 финальная версия для сдачи размещается в:

```text
Co-creation-projects/huailishang-AgentPlatformBase/
```

В сдаче нет `.env`, рабочих данных, кэша, видео, больших моделей и прочих крупных файлов — объём проекта укладывается в лимит 5 МБ.

## Сильные стороны проекта

- Разделение слоя платформы и слоя агентов: новый агент — адаптер и регистрация profile.
- Долгие задачи в фоне: фронтенд не блокируется загрузкой RSS или исследованием DeepResearch.
- RSS с лёгкой инкрементальной стратегией: по умолчанию до 10 источников, 50 статей с текстом и 10 сводок за вызов — без чрезмерной задержки.
- Артефакты и долгосрочные знания в `data/{agent_id}/` — каталог целиком можно игнорировать при коммите.

## Оценка результата

- `smoke_test.py` покрывает health check, список агентов, dry run, защиту от пакетных запросов и базовую цепочку выполнения задач.
- Объём каталога для сдачи ~143 КБ, без рабочих данных и ключей — в пределах лимита 5 МБ.
- Логи RSS в бэкенде сведены к этапам и статистике, без спама по каждой статье.

## Дальнейшие планы

- Полноценная страница просмотра отчётов `deep_research` на фронтенде.
- Фильтры, избранное и архив истории для RSS-дайджеста на фронтенде.
- Персистентность событий задач в SQLite и история после перезапуска сервиса.

## Автор

- Каталог GitHub: `huailishang-AgentPlatformBase`
- Путь проекта: `Co-creation-projects/huailishang-AgentPlatformBase/`

## Лицензия

Проект для выпускной работы курса Hello-Agents; действует лицензия корневого репозитория.
