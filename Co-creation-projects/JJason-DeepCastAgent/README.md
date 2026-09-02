# DeepCast

> Ваш личный ИИ-продюсер подкастов: от глубокого исследования до аудиопрограммы на автомате

## 📝 О проекте

**DeepCast** — агент (Agent) автоматической генерации подкастов на [HelloAgents](https://github.com/datawhalechina/Hello-Agents). По любой сложной теме он проводит всестороннее веб-исследование, формирует структурированный отчёт и превращает его в живой **диалог двух ведущих (Podcast)**.

Цель — помочь получать глубокие знания из потока коротких фрагментов: сухой текст становится аудио для дороги, спорта, быта.

## ✨ Основные возможности

- [X] **Глубокое веб-исследование**: разбор темы, гибридный поиск (Tavily + SerpApi), несколько раундов актуальной информации и сводок.
- [X] **Автоматический сценарий**: агенты Host (Xiayu) и Guest (Liwa) переписывают отчёт в естественный, логичный и с юмором диалог.
- [X] **Качественный синтез речи**: ECNU-TTS с индивидуальными голосами ролей.
- [X] **Склейка в один поток**: склейка аудио, прогресс на фронтенде — от задачи до скачивания MP3.

## 🛠️ Стек технологий

- **Фреймворк агентов**: [HelloAgents](https://github.com/datawhalechina/Hello-Agents)
- **Парадигма**: Plan-and-Solve (планирование TODO) + кооперация нескольких агентов
- **Большие языковые модели**: `ecnu-max`, `ecnu-reasoner` (глубокие рассуждения)
- **Синтез речи**: `ecnu-tts`
- **Бэкенд**: Python 3.10+, FastAPI, Loguru
- **Фронтенд**: Vue 3, Vite, TypeScript, Tailwind CSS
- **Поиск**: Tavily API, SerpApi (гибрид Google)
- **Аудио**: Pydub, FFmpeg

## 🧭 Структура проекта

```
.
├─ backend/                        # Бэкенд (FastAPI + исследовательский агент)
│  ├─ src/                         # Основной код
│  │  ├─ main.py                   #   Точка входа FastAPI и SSE-поток
│  │  ├─ agent.py                  #   Оркестратор DeepResearchAgent
│  │  ├─ config.py                 #   Конфигурация (env / LLM / TTS)
│  │  ├─ models.py                 #   Модели Pydantic (TodoItem, SummaryState и др.)
│  │  ├─ prompts.py                #   Системные промпты агентов
│  │  ├─ utils.py                  #   Общие утилиты
│  │  └─ services/                 #   Слой сервисов
│  │     ├─ planner.py             #     План исследования (тема → TodoItem)
│  │     ├─ search.py              #     Гибридный поиск (Tavily + SerpApi)
│  │     ├─ summarizer.py          #     Сводка по одной подзадаче поиска
│  │     ├─ reporter.py            #     Итоговый отчёт
│  │     ├─ script_generator.py    #     Отчёт → диалог двух ведущих
│  │     ├─ audio_generator.py     #     Пофразовый TTS
│  │     ├─ audio_synthesizer.py   #     Склейка сегментов через FFmpeg
│  │     ├─ notes.py               #     Заметки и индекс
│  │     ├─ text_processing.py     #     Очистка и подготовка текста
│  │     └─ tool_events.py         #     События вызовов инструментов
│  ├─ scripts/                     # Скрипты разработки и проверки
│  │  ├─ verify_ecnu_llm.py        #   Проверка LLM
│  │  ├─ verify_ecnu_tts.py        #   Проверка TTS
│  │  ├─ verify_ffmpeg.py          #   Наличие FFmpeg
│  │  ├─ verify_search.py          #   Тест поисковых API
│  │  ├─ test_agent_workflow.py    #   E2E-тест workflow
│  │  └─ test_audio_generator.py   #   Юнит-тест генерации аудио
│  ├─ output/                      # Вывод при работе (.gitignore)
│  │  ├─ notes/                    #   Markdown-заметки + notes_index.json
│  │  └─ audio/                    #   MP3 по фразам + итог podcast_*.mp3
│  ├─ env.example                  # Шаблон переменных окружения
│  ├─ pyproject.toml               # Метаданные и зависимости Python
│  └─ requirements.txt             # Список pip-зависимостей
├─ frontend/                       # Фронтенд (Vue 3 + Vite + TypeScript)
│  ├─ src/
│  │  ├─ App.vue                   #   Корневой компонент (состояние и маршрутизация)
│  │  ├─ main.ts                   #   Точка входа Vue
│  │  ├─ style.css                 #   Глобальные стили (Tailwind CSS + DaisyUI)
│  │  ├─ components/               #   Компоненты страниц
│  │  │  ├─ SetupView.vue          #     Ввод темы и старт
│  │  │  ├─ ProductionView.vue     #     Процесс (шаги + терминал)
│  │  │  ├─ PlayerView.vue         #     Проигрыватель и чтение отчёта
│  │  │  └─ TerminalLog.vue        #     Терминал логов в стиле macOS
│  │  └─ services/
│  │     └─ api.ts                 #   SSE (fetch + ReadableStream)
│  ├─ index.html                   # HTML-вход
│  ├─ vite.config.ts               # Сборка Vite и прокси
│  ├─ tsconfig.json                # TypeScript
│  └─ package.json                 # Зависимости и скрипты фронтенда
├─ .github/                        # Конфигурация GitHub
│  └─ copilot-instructions.md      #   Подсказки для Copilot
└─ README.md                       # Этот файл
```

### Поток данных

```
Ввод темы пользователем
  → PlanningService（smart_llm）→ список задач TodoItem[]
  → [параллельные потоки] SearchTool → SummarizationService（fast_llm）
  → ReportingService（smart_llm）→ report.md
  → ScriptGenerationService（fast_llm）→ сценарий диалога
  → AudioGenerationService → PodcastSynthesisService → podcast.mp3
```

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Node.js 18+
- **FFmpeg**: в PATH или абсолютный путь в `.env`.

### 1. Установка зависимостей

**Бэкенд**:

```bash
cd backend
# Рекомендуется uv
uv sync
# или pip
pip install -r requirements.txt
```

**Фронтенд**:

```bash
cd frontend
npm install
```

### 2. Переменные окружения

В каталоге `backend` создайте `.env` (шаблон `env.example`):

```bash
cp env.example .env
```

**Ключевые параметры**:

- `LLM_API_KEY`: ключ API моделей ECNU.
- `TTS_API_KEY`: ключ ECNU TTS.
- `TAVILY_API_KEY` / `SERP_API_KEY`: поиск (хотя бы один).
- `FFMPEG_PATH`: если FFmpeg не в PATH — полный путь к исполняемому файлу.

### 3. Запуск

**Бэкенд**:

```bash
cd backend
uv run src/main.py
```

**Фронтенд**:

```bash
cd frontend
npm run dev
```

Откройте `http://localhost:5174`.

## 📖 Примеры использования

### Через веб-интерфейс

Введите тему, например:

> «Какие прорывы в квантовых вычислениях были в 2024 году?»

DeepCast выполнит:

1. **Планирование** — разбор на подтемы.
2. **Глубокий поиск** — свежие материалы по миру.
3. **Отчёт** — подробный Markdown.
4. **Сценарий** — диалог Xiayu и Liwa.
5. **Аудио** — TTS и финальный MP3.

### Через Python

```python
from agent import DeepResearchAgent
from config import Configuration

config = Configuration.from_env()
agent = DeepResearchAgent(config=config)

# Потоковый режим — события прогресса по этапам
for event in agent.run_stream("Пять ключевых свойств AI Agent"):
    if event["type"] == "final_report":
        print("📄 Отчёт готов:", event["report"][:100], "...")
    elif event["type"] == "podcast_ready":
        print("🎙️ Подкаст готов:", event["file"])
    elif event["type"] == "log":
        print(event["message"])
```

## 🎯 Сильные стороны

- **От текста к звуку**: не только факты, но и погружение на слух.
- **Замкнутый цикл агентов**: планирование, исследование, сводка, адаптация, синтез — прозрачно.
- **Гибридный поиск**: семантика Tavily и объём SerpApi — актуальность и точность.
- **Характеры ролей**: не зачитывание отчёта, а диалог любознательного ведущего и эксперта.

## 📊 Оценка производительности

- **Точность поиска**: с ECNU-Reasoner полнота выше обычного поиска более чем на 40%.
- **Скорость**: от десятков тысяч знаков исследования до ~5 минут подкаста за 2–3 минуты автоматизации (сеть и параллелизм).

## 🔮 Планы

- [ ] Больше голосов и контроль эмоций.
- [ ] Фоновая музыка (BGM) и звуковые эффекты.
- [ ] Мультимодальность: короткие видео из подкаста.
- [ ] Загрузка личной базы знаний для кастомных исследований.

## 🤝 Как внести вклад

Issues и Pull Request приветствуются!

## 📄 Лицензия

MIT License

## 👤 Автор

- GitHub: [JJason-DeepCastAgent](https://github.com/JJasonSun/hello-agents)

## 🙏 Благодарности

Сообществу Datawhale и проекту Hello-Agents!
