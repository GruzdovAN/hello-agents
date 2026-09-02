# SoftwareDevHelper — помощник в обучении разработке ПО

> Умный помощник на HelloAgents: запоминает уровень пользователя, выдаёт задачи, тестирует код и оценивает результат.

## 📝 Описание проекта

SoftwareDevHelper для начинающих программистов:
- Запоминает и оценивает уровень
- Генерирует задачи или ищет реальные примеры в сети
- Советы в процессе разработки
- После загрузки архива проекта — автотесты и оценка
- История обучения и баллы

Полная реализация: фронтенд HTML+JavaScript, бэкенд Python (FastAPI) и HelloAgents.

## ✨ Основные возможности

- [x] **Уровень пользователя**: история задач и оценка (боковая панель, общая между сессиями)
- [x] **Генерация задач**: по текущему уровню — свои задачи или поиск кейсов
- [x] **Советы при разработке**: ревью и оптимизация
- [x] **Автотесты и оценка**: распаковка zip, устойчивые тесты (динамический импорт подмодулей, без массового импорта и срабатывания `antigravity`), балл
- [x] **Веб-интерфейс**
- [x] **Несколько сессий**: чаты на бэкенде, удаление из списка; восстановление контекста после перезапуска
- [x] **Визуализация инструментов**: параметры и результаты вызовов в чате

## 🛠️ Технологический стек

- **Агенты**: HelloAgents (SimpleAgent, ToolRegistry)
- **Бэкенд**: FastAPI, Uvicorn
- **Фронтенд**: HTML5, CSS3, Vanilla JavaScript
- **LLM**: интерфейс под разные модели (Qwen и др.)
- **Прочее**: `zipfile`, `pytest` / `unittest`

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Рекомендуется Conda

### Установка

```bash
pip install -r requirements.txt
```

### API-ключи

```bash
cp .env.example .env
```

Пример `.env`:
```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api-inference.modelscope.cn/v1/
LLM_MODEL_ID=Qwen/Qwen2.5-72B-Instruct
```

### Запуск

1. **Активируйте окружение** (conda):
   ```bash
   conda activate hello-agent-homework
   ```

2. **Каталог и PYTHONPATH**:
   ```bash
   cd Co-creation-projects/angelen-SoftwareDevHelper
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

3. **FastAPI**:
   ```bash
   uvicorn src.main:app --reload
   ```

4. **Браузер**: [http://127.0.0.1:8000](http://127.0.0.1:8000)

**💡 Замечания:**
- После правки `.env` перезапустите сервер (`--reload` не всегда подхватывает `.env`)
- Порт занят: `uvicorn src.main:app --reload --port 8001` или `lsof -ti :8000 | xargs kill -9`

## 🎯 Сильные стороны

- Персонализация через память об уровне
- Цикл: задача → тест → оценка
- Разделение фронта и бэкенда

## 👤 Автор

- GitHub: [@angelen](https://github.com/angelen)
- Проект: [SoftwareDevHelper](https://github.com/datawhalechina/hello-agents/tree/main/Co-creation-projects/angelen-SoftwareDevHelper)

## 🙏 Благодарности

Спасибо сообществу Datawhale и проекту Hello-Agents!
