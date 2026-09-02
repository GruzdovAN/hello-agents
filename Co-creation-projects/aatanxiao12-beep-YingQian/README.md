# YingQian — мультиагентный помощник по подбору фильмов

> На базе HelloAgents + TMDB: перед тем как погасить свет, выберите фильм на вечер.

## 📝 Описание проекта

«YingQian» решает проблему «что посмотреть сегодня вечером». Пользователь указывает настроение, компанию, жанры, длительность и другие предпочтения — система через **Pipeline + Tool-use** мультиагентный конвейер ищет кандидатов в реальном каталоге TMDB и выдаёт подборку с обоснованием.

- **Решаемая задача**: разрозненные предпочтения, слишком много вариантов, риск выдуманных названий
- **Особенности**: трёхэтапное взаимодействие агентов + инструменты TMDB для реальных фильмов + проверка по белому списку id
- **Сценарии**: быстрый выбор для себя/пары/друзей; пример оркестрации нескольких агентов в HelloAgents

## ✨ Основные возможности

- [x] Агент профиля: формирует сводку вкусов и поисковые подсказки (TasteProfile)
- [x] Агент поиска: вызывает TMDB `discover` / `search` для реальных кандидатов
- [x] Агент рекомендаций: выбирает только из id кандидатов и пишет обоснование на русском/китайском
- [x] «Другая подборка»: повторный поиск с тем же профилем, исключая уже показанные id
- [x] Просмотр каталога / детали через REST API
- [x] React-фронтенд (бренд «YingQian»)

## 🛠️ Технологический стек

- **HelloAgents**: `SimpleAgent` + Tool (последовательный Pipeline из нескольких агентов)
- **Бэкенд**: FastAPI, Pydantic, httpx
- **Источник данных**: TMDB API
- **Фронтенд**: Vite + React + TypeScript
- **LLM**: OpenAI-совместимый интерфейс (например DeepSeek)

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Node.js 18+ (опционально, для фронтенда)
- TMDB Access Token или API Key
- OpenAI-совместимый LLM (`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL_ID`)

### Установка зависимостей

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r ../requirements.txt
pip install jupyterlab   # если нужен main.ipynb
```

### Настройка API-ключей

**Файл `.env` должен лежать в каталоге `backend/`** (код читает `backend/.env`):

```bash
# из корня проекта aatanxiao12-beep-YingQian/
cp .env.example backend/.env

# Windows PowerShell
# Copy-Item .env.example backend\.env
```

Отредактируйте `backend/.env`, минимум:

```env
TMDB_ACCESS_TOKEN=ваш_TMDB_Token
# или TMDB_API_KEY=ваш_Key

LLM_API_KEY=ваш_LLM_ключ
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_ID=deepseek-v4-flash
```

### Способ A: быстрая демонстрация в Jupyter (рекомендуется для ревью)

```bash
# всё ещё в backend/ с активированным venv
cd ..
jupyter lab
# откройте main.ipynb и выполните ячейки по порядку
```

Notebook вызовет полный конвейер рекомендаций и выведет сводку профиля и список фильмов.

### Способ B: запуск веб-сервиса

```bash
cd backend
python run.py
```

- API: http://127.0.0.1:8000  
- Документация: http://127.0.0.1:8000/docs  

Фронтенд (опционально):

```bash
cd frontend
npm install
npm run dev
```

Откройте в браузере http://127.0.0.1:5173

## 📖 Примеры использования

### 1) Рекомендация одной кнопкой в Notebook

См. `main.ipynb`. Эквивалентный вызов:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("backend").resolve()))

from app.models.schemas import RecommendRequest
from app.agents.movie_recommender_agent import MultiAgentMovieRecommender

req = RecommendRequest(
    mood="расслабиться",
    party_type="один",
    genres=["драма", "комедия"],
    max_runtime_minutes=120,
    region_preference="любой",
    year_preference="последние 10 лет",
    free_text="не слишком тяжёлый",
)
result, trace_id = MultiAgentMovieRecommender().recommend(req)
for m in result.movies:
    print(m.title, m.reason)
```

### 2) HTTP API

```bash
curl -X POST http://127.0.0.1:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d "{\"mood\":\"душевный\",\"party_type\":\"друзья\",\"genres\":[\"романтика\"],\"region_preference\":\"любой\",\"year_preference\":\"последние 10 лет\"}"
```

При успехе возвращается около 5 карточек фильмов (`title`, `poster_url`, `reason` и т.д.) и опционально `taste_profile`.

### 3) Фронтенд

Главная → заполнить предпочтения → «Подобрать фильмы» → на странице результатов смотреть обоснования; можно «Другая подборка» или перейти в «Каталог».

## 🎯 Сильные стороны проекта

- **Только реальные фильмы**: поиск только через TMDB Tool, на этапе рекомендаций — белый список id кандидатов, меньше выдуманных названий
- **Разделение ролей агентов**: профиль / поиск / рекомендации — удобно для обучения и расширения
- **Резервный режим**: при сбое парсинга агента поиска — rule-based discover
- **Полноценный продукт**: не только демо агента, но и FastAPI + фронтенд

## 📊 Производительность (ориентир)

При DeepSeek и доступном TMDB полный цикл рекомендации примерно:

| Этап | Ориентир |
|------|----------|
| Агент профиля | ~5–8 с |
| Агент поиска (1× discover) | ~15–25 с |
| Агент рекомендаций | ~10–15 с |
| **Итого** | **~40–50 с** |

TMDB обычно <2 с; основное время — LLM. Если `api.themoviedb.org` недоступен из вашей сети — нужен прокси/VPN.

## 🔮 Планы развития

- [ ] Rule-based профиль без свободного текста, пропуск одного вызова LLM
- [ ] Discover по умолчанию по правилам, агент поиска только для сложных запросов
- [ ] Фильтрация короткометражек, нижняя граница длительности и др.
- [ ] Прогресс на фронтенде, синхронизированный с этапами

## 📂 Структура проекта

```text
aatanxiao12-beep-YingQian/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── main.ipynb                 # быстрый вход
├── backend/
│   ├── .env.example           # как в корне (удобно положить backend/.env)
│   ├── app/                   # Agents / Tools / API / TMDB
│   ├── tests/
│   ├── run.py
│   └── pyproject.toml
└── frontend/
    ├── src/
    ├── package.json
    └── ...
```

## 🤝 Участие в проекте

Приветствуются Issue и Pull Request!

## 📄 Лицензия

MIT License

## 👤 Автор

- GitHub: [@aatanxiao12-beep](https://github.com/aatanxiao12-beep)

## 🙏 Благодарности

Спасибо сообществу Datawhale и проекту Hello-Agents!
