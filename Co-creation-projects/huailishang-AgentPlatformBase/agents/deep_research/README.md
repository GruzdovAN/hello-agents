# deep_research

`deep_research` — встроенный в платформу chapter16 агент (Agent) поиска и исследований; исходники:

```text
agents/deep_research/src/
```

Код из DeepResearchAgent главы 14, встроен в проект chapter16. По умолчанию запуск не зависит от `code/chapter14` — достаточно `code/chapter16/agent_platform_base` для работы поисковика.

Данные запуска пишутся в:

```text
data/deep_research/runs/
data/deep_research/notes/
```

- `runs/` — артефакты одного запуска, можно чистить по сроку хранения.
- `notes/` — исследовательские заметки и индекс; по умолчанию хранятся долго.
