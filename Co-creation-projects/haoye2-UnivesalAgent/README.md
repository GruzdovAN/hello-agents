# UniversalAgent — универсальная система агентов

> Умный поиск и безопасное выполнение команд на фреймворке Hello-Agents

## 📝 О проекте

Универсальная система на **Hello-Agents**: дизайн **один агент (Agent) + много инструментов**.
Агент регистрирует и вызывает инструменты через ToolRegistry.

### Основные возможности
- ✅ **Умный веб-поиск**: несколько движков и извлечение контента
- ✅ **Безопасный терминал**: 20+ разрешённых команд, проверка аргументов
- ✅ **Память**: предпочтения и важная информация (в планах)
- ✅ **Несколько движков**: DuckDuckGo, Brave, Ecosia, Searx

## 🛠️ Стек технологий

- HelloAgents (SimpleAgent + ToolRegistry)
- Python AST (разбор кода)
- ModelScope API (модели Qwen)
- Beautiful Soup (извлечение с веб-страниц)


## 🚀 Быстрый старт

### Требования

- Python 3.10+
- См. requirements.txt

### Установка

```bash
pip install -r requirements.txt
```

### API-ключ

```bash
cp .env.example .env

LLM_API_KEY=your_api_key_here
```

### Запуск

**Вариант 1: Jupyter Notebook (рекомендуется)**
```bash
jupyter lab
# Откройте main.ipynb
```

**Вариант 2: CLI**
```bash
python main.py
```

## 📖 Примеры

### 1. Умный поиск
```
Ввод: найди последние новости об ИИ в Python
Вывод: результаты поиска и краткое содержание
```

### 2. Команды терминала
```
Ввод: pwd
Вывод: /Users/qinbohua/Developing/universal_hello_agent_llm_decision

Ввод: ls -la
Вывод: total 48... (список файлов)

Ввод: mkdir test_project && cd test_project
Вывод: каталог создан, переход выполнен

Ввод: grep -n "import" src/
output: src/agents/agent_universal.py:1:from hello_agents
```

### 3. Сложная задача
```
Ввод: найди последнюю версию LangChain и покажи файлы в текущем каталоге
Вывод: сначала поиск, затем список файлов и сводка
```

## 📂 Структура проекта

```
universal_hello_agent_llm_decision/
├── README.md              # Документация
├── requirements.txt       # Зависимости Python
├── main.ipynb            # Основной Notebook
├── main.py               # CLI (опционально)
├── data/                 # Данные (опционально)
│   └── sample_queries.txt
├── outputs/              # Результаты (опционально)
│   ├── demo_results.md
│   ├── docs/
│   │   ├── CONTRIBUTING.md
│   │   └── IMPROVEMENTS_SUMMARY.md
│   └── tests/
│       ├── test_agent_improvements.py
│       └── test_tools.py
└── src/
    ├── __init__.py
    ├── agents/
    │   ├── __init__.py
    │   ├── agent_universal.py
    │   └── config.py
    ├── tools/
    │   ├── __init__.py
    │   ├── browser_tool.py
    │   └── terminal_tool.py
    └── utils/
        └── __init__.py
```

## 🎯 Преимущества

- **Модульность**: инструменты и агенты разделены
- **Безопасность**: многоуровневая защита
- **Отказоустойчивость**: деградация и восстановление
- **Совместимость**: стандарт Hello-Agents
- **Поиск**: 4 движка с переключением

## 🔮 Планы

- [ ] Больше инструментов (файлы, БД)
- [ ] Полноценная память
- [ ] Ускорение поиска
- [ ] Web-интерфейс
- [ ] Мультиагентное взаимодействие

## 🤝 Как внести вклад

Issue и Pull Request приветствуются!

## 📄 Лицензия

MIT License

## 👤 Автор

- GitHub: [@haoye2](https://github.com/haoye2)
- Проект: [UniversalAgent](https://github.com/datawhalechina/Hello-Agents/tree/main/Co-creation-projects/haoye2-UniversalAgent)

## 🙏 Благодарности

Сообществу Datawhale и проекту Hello-Agents!

---

## 📚 Подробнее

### Инструмент браузерного поиска

#### Движки
- **DuckDuckGo**: стабильный HTML-поиск
- **Brave**: современный поиск
- **Ecosia**: экологичный поиск
- **Searx.xyz**: метапоиск с открытым кодом

#### Умные функции
- **8 с на таймаут**: единый лимит ожидания
- **Тихий failover**: быстрое переключение движка
- **Деградация**: подсказки поиска как запасной вариант
- **Проверка качества**: фильтрация результатов
- **Извлечение контента**: 5 уровней для основного текста страницы

### Конфигурация

`config.py` — единая настройка инструментов.

#### Режим безопасности терминала
```python
# config.py
TERMINAL_SECURITY_MODE = "strict"  # или "warning"
```
- **strict**: опасные команды блокируются (рекомендуется в продакшене)
- **warning**: предупреждение (для отладки)

Подробнее: [CONFIG_GUIDE.md](./CONFIG_GUIDE.md)

### Безопасность

- Не публикуйте реальные API Key в открытых репозиториях.
- `terminal_exec` выполняет только команды из белого списка; предпочтительно контейнер или изолированная среда.
- Парсинг DuckDuckGo HTML — для демо; в продакшене используйте Search API (SerpApi/Tavily и т.д.).

### Устранение неполадок

- Ошибки LLM: проверьте `LLM_API_BASE` и `LLM_API_KEY` в `.env`.
- Замена на SerpApi: см. `src/tools/browser_tool.py` и добавьте ключ.
- Конфигурация: [CONFIG_GUIDE.md](./CONFIG_GUIDE.md)
