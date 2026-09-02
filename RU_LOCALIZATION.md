# Русская редакция Hello-Agents — что переведено

Локальная русская редакция ядра курса [Hello-Agents](https://github.com/datawhalechina/Hello-Agents) (Datawhale).  
Цель: одна локаль для обучения — **русский**, без параллельных EN/CN копий в ядре.

Дата локализации ядра: август 2026 (коммит `fa8380b`).  
Доп. волна Extra P0/P1: август 2026.

---

## Принципы

1. **Одна локаль в ядре**  
   Не добавляли третий язык рядом с EN/CN. После перевода EN/CN-дубликаты глав и навигации удалены.

2. **Источник перевода**  
   - Главы учебника — с английских `ChapterN-*.md` / `Preface.md`.  
   - Код и CN-only README — с китайского (комментарии, docstring, учебные промпты, гайды).

3. **Термины**  
   При первом упоминании — русский + привычный EN в скобках, где уместно: **агент (Agent)**, **ReAct**, **MCP**.  
   Имена API, библиотек, ключей JSON, идентификаторов кода **не русифицировали**.

4. **Что считается «учебным текстом»**  
   Переводили: прозу глав, README курса, сайдбар Docsify, UI Docsify, комментарии `#`, docstring, человекочитаемые `print`/логи, учебные промпты, markdown-гайды в `code/`.  
   Не переводили: имена функций/классов/переменных, импорты, чужие лицензии, бинарники/картинки (подписи в MD — да).

5. **Код в fence-блоках глав**  
   Примеры кода в ` ``` ` внутри глав могут оставаться на EN (идентификаторы и API).  
   Китайские **комментарии** в примерах README/`code` переведены.

6. **Качество**  
   Перевод в основном машинный с последующей дочисткой хвостов. Возможны шероховатости формулировок; смысловая правка по главам — по запросу.

---

## Что переведено

| Область | Содержание |
|--------|------------|
| Корень | [`README.md`](README.md) — на русском; `README_EN.md` удалён |
| Docsify | [`docs/index.html`](docs/index.html) — только RU (без переключателя CN↔EN) |
| Навигация | [`docs/_sidebar.md`](docs/_sidebar.md), [`docs/README.md`](docs/README.md), [`docs/Preface.md`](docs/Preface.md) |
| Главы 1–16 | Файлы `docs/chapterN/ChapterN-*.md` — текст на русском, ASCII-имена |
| Учебный код | Комментарии, docstring, промпты, сообщения в `code/chapter1`–`16` |
| Гайды в `code/` | README и гайды проектов (в т.ч. trip-planner, AI-Town, chapter9/12 и др.) |
| Notebook | [`code/chapter1/FirstAgentTest.ipynb`](code/chapter1/FirstAgentTest.ipynb) |
| Переименования | `共创路径.md` → `code/chapter16/co-creation-path.md`; `运行指南.md` → `code/chapter12/data_generation/run-guide.md` |
| Extra P0/P1 | [`Extra-Chapter/`](Extra-Chapter/) — см. таблицу ниже; ASCII-имена, одна RU-локаль |
| Co-creation-projects | [`Co-creation-projects/`](Co-creation-projects/) — README ~46 проектов, UI, промпты; пилот `YYHDBL-HelloCodeAgentCli` |
| Co-creation-projects | README ~46 проектов, доп. docs, UI full-stack, промпты и runtime-строки; пилот `YYHDBL-HelloCodeAgentCli` |

Структура глав после локализации: **один файл на главу** (без пары CN+EN).

### Extra-Chapter (переведено)

| RU-файл | Было (CN) |
|---------|-----------|
| [`Extra01-Interview-Questions.md`](Extra-Chapter/Extra01-Interview-Questions.md) | `Extra01-面试问题总结.md` |
| [`Extra01-Reference-Answers.md`](Extra-Chapter/Extra01-Reference-Answers.md) | `Extra01-参考答案.md` |
| [`Extra02-Context-Engineering-Supplement.md`](Extra-Chapter/Extra02-Context-Engineering-Supplement.md) | `Extra02-上下文工程补充知识.md` |
| [`Extra04-Datawhale-FAQ.md`](Extra-Chapter/Extra04-Datawhale-FAQ.md) | `Extra04-DatawhaleFAQ.md` |
| [`Extra05-Agent-Skills.md`](Extra-Chapter/Extra05-Agent-Skills.md) | `Extra05-AgentSkills解读.md` |
| [`Extra08-How-to-Write-Good-Skills.md`](Extra-Chapter/Extra08-How-to-Write-Good-Skills.md) | `Extra08-如何写出好的Skill.md` |
| [`Extra09-Agent-Dev-Pitfalls-and-Lessons.md`](Extra-Chapter/Extra09-Agent-Dev-Pitfalls-and-Lessons.md) | `Extra09-Agent应用开发实践踩坑与经验分享.md` |
| [`Extra10-Agent-Self-Evolution.md`](Extra-Chapter/Extra10-Agent-Self-Evolution.md) | `Extra10-Agent自进化.md` |

Навигация Extra: [`Extra-Chapter/readme.md`](Extra-Chapter/readme.md).

---

## Что не переведено и почему

| Область | Почему |
|--------|--------|
| Extra03 / 06 / 07 / 11 / 12 / 13 | Низкий ROI для обучения: дубли гл. 5, env уже в `code/`, GUI/Web/post-train — расширение за ядро, видео — орг. CN-ссылки |
| [`Additional-Chapter/`](Additional-Chapter/) | Короткие гайды Node/n8n; достаточно внешних docs |
| Сгенерированные отчёты | `template_output/`, `evaluation_results/`, `generated_data/` — артефакты прогонов, не учебник |
| Идентификаторы кода | Совместимость с API/фреймворками; перевод ломал бы запуск |
| Картинки в `docs/images/` и Extra | Без смены ассетов; подписи в MD — на русском |

---

## Как читать локально

1. Открыть [`docs/index.html`](docs/index.html) через Docsify (или статический сервер из `docs/`).  
2. Либо читать markdown в `docs/chapter*/` и код в `code/`.

Оригинал upstream (CN/EN): https://github.com/datawhalechina/Hello-Agents  

---

## Известные ограничения

- Машинный перевод: стиль местами неровный.  
- В примерах кода EN-идентификаторы и EN-строки API намеренно сохранены.  
- В AI-Town имена NPC в примерах локализованы (например, 张三 → Чжан Сань) для читаемости гайдов.
