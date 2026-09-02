# Угадай, кто я (GuessWhoAmI)

Интерактивная игра «угадай персонажа» на фреймворке `hello_agents`. Агент (Agent) случайно играет историческую, мифическую фигуру или интернет-знаменитость; пользователь угадывает через серию вопросов.

## Особенности проекта

- 🤖 **Динамическая генерация персонажа LLM** — в каждой партии модель создаёт нового персонажа: Восток и Запад, история, миф, вымысел, блогеры; без повторов
- 🎭 **Погружение в роль** — агент отвечает от первого лица, в тоне эпохи и характера; ответы с намёками и отвлечениями
- 🔍 **Поиск Tavily** — автоматический поиск сведений о персонаже, три подсказки от общего к конкретному
- 🖼️ **Картинка после угадывания** — поиск изображения через Wikipedia
- 🧠 **Семантическое сравнение** — LLM определяет, совпадает ли догадка (псевдонимы, прозвища)
- ⚡ **Бэкенд FastAPI** + современный веб-фронтенд

## Структура проекта

```
afei-GuessWhoAmI/
├── restart.sh               # запуск фронта и бэка одной командой
├── backend/
│   ├── main.py              # FastAPI, маршруты API
│   ├── agents.py            # логика агента (генерация, роль, проверка догадки)
│   ├── game_logic.py        # состояние игры (GameSession)
│   ├── config.py            # настройки (синглтон Settings)
│   ├── models.py            # Pydantic-модели запросов/ответов
│   ├── requirements.txt     # зависимости Python
│   ├── .env.example         # шаблон переменных окружения
│   └── tools/
│       ├── tavily_search_tool.py   # Tavily (подсказки)
│       └── search_image_tool.py    # Wikipedia (картинки)
├── frontend/
│   ├── index.html           # главная страница
│   ├── style.css            # стили
│   └── app.js               # логика UI
└── logs/
    ├── backend.log          # лог бэкенда
    └── frontend.log         # лог фронтенда
```

## Требования

- Python 3.8+
- ModelScope API Key (обязательно)
- Tavily API Key (обязательно, для подсказок: https://app.tavily.com/)

## Быстрый старт

### 1. Установка зависимостей

```bash
cd /home/afei/hello-agents/Co-creation-projects/afei-GuessWhoAmI/backend
pip install -r requirements.txt
```

### 2. Переменные окружения

```bash
cp backend/.env.example backend/.env
```

Содержимое `backend/.env`:

```env
# LLM (ModelScope API, обязательно)
LLM_MODEL_ID=qwen-flash
LLM_API_KEY=your_modelscope_api_key
LLM_BASE_URL=https://api-inference.modelscope.cn/v1/
LLM_TIMEOUT=180

# Tavily (обязательно)
# Ключ: https://app.tavily.com/
TAVILY_API_KEY=your_tavily_api_key
```

### 3. Запуск одной командой (рекомендуется)

```bash
cd /home/afei/hello-agents/Co-creation-projects/afei-GuessWhoAmI
bash restart.sh
```

Скрипт:
- останавливает старые процессы
- поднимает бэкенд (FastAPI, порт **8000**)
- поднимает фронтенд (Python http.server, порт **3000**)
- ждёт готовности и печатает URL

Пример вывода:
```
✅ All services started successfully!

  🔧 Backend  → http://localhost:8000
  🔧 API Docs → http://localhost:8000/docs
  🌐 Frontend → http://localhost:3000
```

### 4. Адреса

| Сервис | URL |
|------|------|
| 🌐 Игра | http://localhost:3000 |
| 🔧 API | http://localhost:8000 |
| 📖 Документация API | http://localhost:8000/docs |

### 5. Ручной запуск (опционально)

```bash
# бэкенд
cd backend
python main.py

# фронтенд (другой терминал)
cd frontend
python -m http.server 3000
```

## API

| Метод | Путь | Описание |
|------|------|------|
| `POST` | `/api/game/start` | Новая игра (LLM генерирует персонажа и подсказки) |
| `POST` | `/api/game/chat` | Вопрос агенту (ролевая беседа) |
| `POST` | `/api/game/guess` | Догадка (семантическая проверка; при успехе — картинка) |
| `GET`  | `/api/game/hint` | Следующая подсказка |
| `POST` | `/api/game/end` | Завершить игру |
| `GET`  | `/api/game/status` | Статус текущей игры |

## Правила игры

1. «Начать игру» — LLM выбирает персонажа (история, миф, вымысел, блогер)
2. Задавайте вопросы; агент отвечает от первого лица и **не называет имя напрямую**
3. До **10** вопросов и **3** подсказок (от общего к конкретному)
4. Догадку можно отправить в любой момент; учитываются псевдонимы
5. При угадывании — картинка; при исчерпании вопросов или завершении — ответ

## Технологический стек

### Бэкенд
- **FastAPI** — веб-фреймворк
- **hello_agents** — агент (Agent) (SimpleAgent, HelloAgentsLLM)
- **Pydantic v2** — валидация
- **Uvicorn** — ASGI-сервер
- **Tavily Python SDK** — поиск
- **Wikipedia API** — изображения

### Фронтенд
- **HTML5 / CSS3 / JavaScript** — без фреймворков
- **Fetch API** — запросы к бэкенду

### AI / LLM
- **ModelScope API** — OpenAI-совместимый интерфейс (по умолчанию `qwen-flash`)
- **Генерация персонажа** — случайность, без повторов
- **Семантическое сравнение** — одна и та же личность при разных формулировках

## Конфигурация

| Параметр | По умолчанию | Описание |
|--------|--------|------|
| `LLM_MODEL_ID` | `qwen-flash` | Модель LLM (flash — меньше задержка) |
| `LLM_BASE_URL` | ModelScope API | URL LLM |
| `LLM_TIMEOUT` | `180` | Таймаут запроса (с) |
| `TAVILY_API_KEY` | нет | Ключ Tavily (обязательно), https://app.tavily.com/ |
| `MAX_QUESTIONS` | `10` | Макс. вопросов за партию |
| `MAX_HINTS` | `3` | Макс. подсказок за партию |

## Логи

Каталог `logs/`:

```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

## Устранение неполадок

**Сбой LLM**
- Проверьте `LLM_API_KEY` и `LLM_BASE_URL` в `backend/.env`
- Доступ к модели в ModelScope

**Один и тот же персонаж**
- Используются случайное зерно и метка времени; проверьте поддержку случайности у модели

**Tavily недоступен**
- Проверьте `TAVILY_API_KEY`
- Без ключа — упрощённые подсказки, ниже качество
- Ключ: https://app.tavily.com/

**Порт занят**
- `restart.sh` освобождает порты; запустите снова

**CORS**
- Бэкенд разрешает все источники; фронтенд должен ходить на порт 8000
