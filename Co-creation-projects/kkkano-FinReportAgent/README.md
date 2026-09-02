# FinReportAgent — агент финансовых отчётов

> Агент генерации финансовых отчётов на HelloAgents: сбор данных из нескольких источников и инвестиционный анализ

## О проекте

FinReportAgent — агент (Agent) на [HelloAgents](https://github.com/datawhalechina/hello-agents) для отчётов по рынку. Он:

- **Собирает данные автоматически**: DuckDuckGo, Yahoo Finance API — котировки и новости
- **Анализирует с рассуждениями**: парадигма ReAct (Reasoning and Acting) — многошаговый профессиональный анализ
- **Формирует отчёт**: структурированный Markdown с оценкой настроения рынка

## Основные возможности

- 📊 **Котировки** — Yahoo Finance в реальном времени
- 📰 **Финансовые новости** — DuckDuckGo News
- 🔍 **Поиск по сети** — DuckDuckGo
- 📄 **Отчёт Markdown** — структурированный инвестиционный анализ
- 📈 **Настроение** — бычий / медвежий / нейтральный сигнал

## Стек технологий

| Компонент | Технология |
|------|------|
| Фреймворк агентов | [HelloAgents](https://github.com/datawhalechina/hello-agents) |
| Парадигма | ReAct (Reasoning and Acting) |
| Поиск | DuckDuckGo Search |
| Финансовые данные | Yahoo Finance API (yfinance) |
| LLM | DeepSeek / API, совместимый с OpenAI |

## Быстрый старт

### Требования

- Python 3.10+
- Jupyter Notebook / JupyterLab

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка API-ключей

**Способ 1: файл `.env` (рекомендуется)**

```bash
# Скопировать шаблон конфигурации
cp .env.example .env

# Отредактировать .env и указать API-ключ
```

**Способ 2: в Notebook**

Откройте `main.ipynb`, в первой ячейке:
```python
os.environ["LLM_API_KEY"] = "your-api-key-here"  # замените на свой API Key
```

### Запуск

```bash
# Запустить Jupyter
jupyter lab

# Открыть main.ipynb и выполнить все ячейки по порядку
```

## Структура проекта

```
kkkano-FinReportAgent/
├── main.ipynb         # Основная программа
├── README.md          # Описание проекта
├── requirements.txt   # Зависимости
└── .env.example       # Пример переменных окружения
```

## Компоненты HelloAgents

| Компонент | Назначение |
|------|------|
| `ReActAgent` | Цикл ReAct (рассуждение — действие — наблюдение) |
| `HelloAgentsLLM` | Единый интерфейс вызова LLM |
| `ToolRegistry` | Регистрация и управление инструментами |
| `Tool` / `ToolParameter` | Базовые классы описания инструментов |

## Лицензия

MIT License

## Автор

- **Имя**: kkkano
- **GitHub**: [@kkkano](https://github.com/kkkano)
- **Дата**: 2026-01-25

## Благодарности

- Сообществу [Datawhale](https://github.com/datawhalechina)
- [Фреймворку HelloAgents](https://github.com/datawhalechina/hello-agents) — инфраструктура разработки агентов
