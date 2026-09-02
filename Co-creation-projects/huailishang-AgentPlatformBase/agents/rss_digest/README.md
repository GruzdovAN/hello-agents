# RSS Digest

Минимально рабочий инструмент ежедневного дайджеста для чтения:

- загрузка RSS/Atom-лент;
- извлечение основного текста статей;
- краткое изложение на китайском через API, совместимый с OpenAI (SiliconFlow);
- опционально полный перевод на китайский;
- ежедневный HTML-дайджест для быстрого просмотра.

## Структура каталогов

```text
rss_digest/
├─ config/
│  ├─ sources.json
│  └─ sources_full.opml
├─ data/
│  ├─ raw/
│  ├─ extracted/
│  ├─ translated/
│  └─ digests/
├─ scripts/
│  └─ run_daily.ps1
├─ src/
│  └─ rss_digest/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ db.py
│     ├─ digest.py
│     ├─ extractor.py
│     ├─ feeds.py
│     ├─ llm.py
│     └─ pipeline.py
├─ state/
├─ .env
├─ .env.example
└─ main.py
```

## Переменные окружения

В `rss_digest/.env`:

```env
LLM_MODEL_ID=Qwen/Qwen3-235B-A22B-Instruct-2507
LLM_API_KEY=sk-xxxxx
LLM_BASE_URL=https://api.siliconflow.cn/v1
DISABLE_SYSTEM_PROXY=true
# PROXY_URL=http://127.0.0.1:7890
FETCH_FULL_TRANSLATION=false
MAX_ARTICLES_PER_RUN=12
REQUEST_TIMEOUT_SECONDS=30
```

Пояснения:
- Читаются только переменные `LLM_*`.
- По умолчанию сбрасывается системный прокси, унаследованный процессом, чтобы не блокировать запросы.
- При необходимости прокси задайте `PROXY_URL` в `.env`.
- По умолчанию только краткое изложение на китайском, без полного перевода.
- При `FETCH_FULL_TRANSLATION=true` дополнительно генерируется полный перевод статей — выше стоимость.

## Запуск

В каталоге `D:\SoftWare\pycharm\Project\regularTest`:

```powershell
.venv\Scripts\python.exe rss_digest\main.py
```

Или напрямую:

```powershell
powershell -ExecutionPolicy Bypass -File .\rss_digest\scripts\run_daily.ps1
```

## Результаты

- Файл состояния: `rss_digest\state\articles.json`
- HTML-дайджест за день: `rss_digest\data\digests\digest_YYYY-MM-DD.html`

## Текущий объём реализации

- Базовая загрузка RSS/Atom
- Извлечение текста и базовая очистка
- Генерация краткого изложения на китайском
- HTML-дайджест

## Рекомендации на следующий шаг

Для стабильного качества приоритетно:

1. Подключить `trafilatura` для извлечения основного текста
2. Добавить к сводкам теги категорий и метки «читать внимательно / можно пропустить»
3. Настроить планировщик Windows для ежедневного автозапуска
