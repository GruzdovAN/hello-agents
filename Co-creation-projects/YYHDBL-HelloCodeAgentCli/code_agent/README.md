# Code Agent (HelloAgents CLI)

Простой Code Agent CLI на компонентах **HelloAgents** (`HelloAgentsLLM` / `ContextBuilder` / `ReActAgent` / `TerminalTool` / `NoteTool` / `MemoryTool`). Цель — опыт как у Claude Code/Codex: многоходовый диалог, исследование репозитория по необходимости, патчи с подтверждением перед записью на диск.

## Быстрый старт

1) Зависимости и переменные окружения (рекомендуется `.env`, не коммитить):

- Зависимости: установить `requirements-mvp.txt` из корня репозитория курса
- В корне создать `.env` (см. `.env.example`), минимум:
  - `DEEPSEEK_API_KEY=...` (или ключ другого OpenAI-совместимого провайдера)
  - Опционально: `LLM_MODEL_ID=deepseek-chat`, `LLM_BASE_URL=https://api.deepseek.com`

2) Запуск CLI (рабочая область по умолчанию `.`):

```bash
python3 -m code_agent.hello_code_cli --repo .
```

Команды:
- `:quit` — выход
- `:plan <цель>` — принудительно сгенерировать план (обычно модель вызывает `plan[...]` по необходимости)

## Реализовано (текущая версия)

- Многоходовый диалог: на базе `SimpleAgent`, хранится недавняя история.
- Парадигма агента (Agent): ядро `ReActAgent` (рассуждение + инструменты), планирование — опциональный инструмент `plan[...]`.
- Инженерия контекста: `ContextBuilder` (GSSC) объединяет системные инструкции, историю, заметки, эпизодическую память с контролем бюджета токенов.
- Исследование по необходимости (как Claude Code):
  - Без полного сканирования по умолчанию; `TerminalTool` только при нужде в доказательствах (`ls`/`rg`/`sed`/`cat`, узкий охват).
- Инструменты:
  - `TerminalTool` — просмотр и поиск (`rg`/`grep`/`find`/`cat`/`head`/`tail`/`sed` и т.д.), усиленная безопасность:
    - По умолчанию shell-семантика (пайпы и т.п.)
    - Перенаправление / подстановка команд / опасные команды — подтверждение (`allow_dangerous=true` + интерактив)
    - `git` по умолчанию только `status`/`diff`; `git reset --hard` — явное разрешение
    - `rm`/`chmod` и прочее высокого риска — отказ до подтверждения
  - `NoteTool` — структурированные заметки в `<repo>/.helloagents/notes/` (решения, блокеры, действия).
  - `MemoryTool` — только `episodic` (SQLite), по умолчанию `<repo>/.helloagents/memory/`.
- Запись патчей:
  - Модель выводит патч `*** Begin Patch ... *** End Patch`.
  - CLI применяет; для рискованных (напр. `*** Delete File:` или крупные изменения) — повторный запрос `y/n`.
  - Применение через `code_agent/executors/apply_patch_executor.py`: атомарная запись, бэкап, проверка конфликтов, лимиты размера.

## Ограничения

- Подтверждение чувствительных операций: `Delete File`, `git reset --hard`, `rm`/`chmod`, крупные изменения; более тонкие правила — позже.
- `TerminalTool` принимает строку команды, но выполнение argv-only с перехватом shell внутри инструмента.
- Хранилище по умолчанию `<repo>/.helloagents/` (notes/memory/sessions/logs), переопределение:
  - `HELLOAGENTS_DIR=.helloagents`
  - `CODE_AGENT_MAX_STEPS=8`

## Связанные файлы

- Вход CLI: `code_agent/hello_code_cli.py`
- Логика агента и контекст: `code_agent/agentic/code_agent.py`
- Исполнитель патчей: `code_agent/executors/apply_patch_executor.py`
- Документация по контексту: `docs/chapter9/` (глава 9 курса)
