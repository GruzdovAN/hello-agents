# LearningAgent — AI-помощник в обучении

> Персональный помощник на HelloAgents: планы обучения, заметки и прогресс через диалог с ИИ

## 📝 О проекте

LearningAgent помогает учиться:

- **Системное обучение**: путь по описанию области, репозиторию GitHub или научной статье
- **Управление знаниями**: классификация и теги заметок; ввод текстом, файлом или URL
- **Интерактив**: закрепление через диалог — свободный режим и структурированный тест
- **Прогресс**: оценка по плану, заметкам и сессиям

**Сценарии**: программирование, навыки, статьи, разбор open source

## ✨ Основные возможности

- [x] **План обучения** — по области, GitHub или PDF
- [x] **Умные заметки** — LLM: анализ, категории, теги; текст / файл / URL
- [x] **Интерактив** — Free и Quiz
- [x] **Оценка прогресса** — отчёт по плану, заметкам и сессиям
- [x] **Потоковый вывод** — ответы в реальном времени

## 🛠️ Стек

- **HelloAgents**:
  - SimpleAgent (MainAgent, SummaryAgent)
  - ReActAgent (CreatePlanAgent)
  - ReflectionAgent (VibeLearningAgent)
- **Специалисты**: RepoAnalyzerAgent, PaperAnalyzerAgent, QuizGeneratorAgent
- **Ядро**:
  - Трёхуровневая архитектура агентов
  - Гибридное обновление сводки (<5 файлов — полная перезапись, ≥5 — инкремент)
  - Потоковый вывод
- **LLM**: OpenAI, DeepSeek, Qwen, ModelScope и др. (10+)
- **Инструменты**: pytest, black, mypy, flake8

## 🚀 Быстрый старт

### Требования

- Python 3.10+
- Conda (рекомендуется) или venv

### Установка

```bash
git clone https://github.com/Yixiang-Wu/learningAgent.git
cd learningAgent

conda create -n learning-agent python=3.10
conda activate learning-agent

pip install -r requirements.txt
```

### API-ключ

```bash
cp .env.example .env

# LLM_MODEL_ID=gpt-4o-mini
# LLM_API_KEY=your_api_key_here
# LLM_BASE_URL=https://api.openai.com/v1
```

### Запуск

```bash
python main.py

> /help                    # Справка
> /create Python           # План обучения
> /add Python # декораторы # Заметка
> /vibe Python             # Интерактив
> /vibe Python --mode quiz # Тест
> /summary Python          # Сводка
> /list                    # Список областей
> /exit                    # Выход
```

## 📖 Примеры

### Пример 1: план обучения

```bash
> /create Python
```

ИИ спросит цель, проанализирует область/GitHub/PDF, подберёт ресурсы и сохранит план в `~/.learningAgent/{domain}/plan.md`

**Фрагмент плана**:
```markdown
# План обучения Python

## Обзор области
Python — язык высокого уровня...

## Чеклист предварительных знаний
- [ ] Базовые понятия компьютера
- [ ] Логическое мышление

## Поэтапный путь
### Этап 1: основы Python (2–3 недели)
- Переменные и типы
- Управление потоком и функции
...

## Рекомендуемые ресурсы
- Книга: «Automate the Boring Stuff with Python»
- Курс: официальный tutorial Python
...
```

### Пример 2: заметки

```bash
# Текст
> /add Python # паттерн декоратор
> /add Машинное обучение Дерево решений — алгоритм с учителем...

# Файл
> /add ~/notes/react-hooks.md

# URL
> /add https://blog.example.com/post
```

ИИ: определит область, извлечёт концепции и теги, имя с timestamp, сохранит в `~/.learningAgent/{domain}/knowledge/`, обновит сводку.

**Пример структуры**:
```
~/.learningAgent/
├── Python/
│   ├── knowledge/
│   │   ├── 20250111-алгоритмы-Python-декораторы.md
│   │   └── 20250111-общее-list-comprehension.md
│   └── knowledge_summary.md
```

### Пример 3: интерактив

```bash
> /vibe Python
> /vibe Python --mode quiz
```

**Free**: открытые вопросы, гибкий диалог, углубление.

**Quiz**: структурированные вопросы, оценка ответов, рост сложности.

Сессии логируются и суммируются.

### Пример 4: сводка

```bash
> /summary Python
```

Отчёт: уровень и % освоения, сильные и слабые темы, следующие шаги, общие рекомендации.

## 🎯 Сильные стороны

### 1. Три уровня агентов

- **Координация (L1)**: MainAgent — намерения и маршрутизация
- **Функции (L2)**: CreatePlanAgent, VibeLearningAgent, SummaryAgent
- **Специалисты (L3)**: RepoAnalyzerAgent, PaperAnalyzerAgent, QuizGeneratorAgent

### 2. Гибридное обновление сводки

- **< 5 файлов**: полная перезапись
- **≥ 5 файлов**: инкремент

### 3. Потоковый вывод

- Определение возможностей терминала
- Вкл/выкл в конфиге
- Корректная обработка чанков

### 4. Умные заметки

- Анализ и классификация LLM
- Текст / файл / URL
- Теги и структурированная сводка

### 5. Тесты

- Unit > 80% покрытия
- Интеграционные и live

## 📊 Структура проекта

```
learningAgent/
├── core/                      # Инфраструктура
│   ├── main_agent.py          # MainAgent (координация)
│   ├── file_manager.py        # Файлы
│   └── summary_manager.py       # Сводки (гибрид)
├── agents/                    # Бизнес-логика
│   ├── create_plan_agent.py   # План (ReAct)
│   ├── vibe_learning_agent.py # Интерактив (Reflection)
│   └── summary_agent.py       # Итог (Simple)
├── specialist/                # Специалисты
│   ├── repo_analyzer.py       # GitHub
│   ├── paper_analyzer.py      # PDF
│   └── quiz_generator.py      # Тесты
├── processors/
│   └── add_knowledge.py       # Добавление заметок
├── cli/
│   └── repl.py                # REPL
├── utils/
│   ├── streaming.py
│   ├── error_handlers.py
│   └── exceptions.py
├── tests/
├── main.py
├── requirements.txt
└── README.md
```

## 🧪 Тесты

```bash
pytest tests/ -v
pytest tests/test_agents/test_create_plan_agent.py -v
pytest tests/ --cov=. --cov-report=term-missing
```

## 🔮 Планы

- [ ] Web UI (FastAPI + Vue)
- [ ] Несколько языков интерфейса
- [ ] Экспорт отчёта в PDF
- [ ] Больше LLM-провайдеров
- [ ] Визуализация прогресса
- [ ] Обмен планами в сообществе

## 🤝 Участие

Issue и PR приветствуются.

### Процесс

1. Fork
2. Ветка `feature/AmazingFeature`
3. Коммит `feat: Add some AmazingFeature`
4. Push и Pull Request

### Стиль кода

- `black`, `mypy`, `flake8`
- Unit-тесты для нового кода

## 📄 Лицензия

MIT License

## 👤 Автор

- GitHub: [@Yixiang-Wu](https://github.com/Yixiang-Wu)
- Проект: [learningAgent](https://github.com/Yixiang-Wu/learningAgent)

## 🙏 Благодарности

- [Datawhale](https://github.com/datawhalechina)
- [Hello-Agents](https://github.com/datawhalechina/hello-agents)
- Участникам и ученикам

---

**Примечание**: выпускной проект курса Hello-Agents — пример полноценного многоагентного приложения на HelloAgents.
