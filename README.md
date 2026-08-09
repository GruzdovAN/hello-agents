<div align='center'>
  <img src="./docs/images/hello-agents.png" alt="Hello-Agents" width="100%">
  <h1>Hello-Agents</h1>
  <h3>🤖 «Создаём агентные системы с нуля»</h3>
  <div align="center">
  <a href="https://trendshift.io/repositories/15520" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/15520" alt="datawhalechina%2Fhello-agents | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/>
  </a>
  </div>
  <p><em>От теории к практике: проектирование и реализация агентных систем</em></p>
  <img src="https://img.shields.io/github/stars/datawhalechina/Hello-Agents?style=flat&logo=github" alt="GitHub stars"/>
  <img src="https://img.shields.io/github/forks/datawhalechina/Hello-Agents?style=flat&logo=github" alt="GitHub forks"/>
  <img src="https://img.shields.io/badge/language-Russian-brightgreen?style=flat" alt="Language"/>
  <a href="https://github.com/datawhalechina/Hello-Agents"><img src="https://img.shields.io/badge/GitHub-Project-blue?style=flat&logo=github" alt="GitHub Project"></a>
  <a href="https://datawhalechina.github.io/hello-agents/"><img src="https://img.shields.io/badge/Online%20Reading-green?style=flat&logo=gitbook" alt="Online Reading"></a>
</div>

---

## О проекте

&emsp;&emsp;Если 2024-й был годом «битвы сотен моделей», то 2025-й без сомнения открыл «Год агентов». Фокус технологий смещается с обучения всё более крупных фундаментных моделей на создание более умных агентных приложений. Систематических практико-ориентированных курсов при этом крайне мало. Поэтому мы запустили Hello-Agents — руководство по построению агентных систем с нуля, где теория и практика уравновешены.

&emsp;&emsp;Hello-Agents — **систематический курс по агентам** сообщества Datawhale. Сегодня разработку агентов условно делят на два направления: инженерные агенты вроде Dify, Coze и n8n (по сути процесс-ориентированная разработка, где LLM — бэкенд обработки данных) и AI-native агенты, по-настоящему управляемые ИИ. Этот курс ведёт к глубокому пониманию и построению вторых — настоящих AI Native Agents. Вы пройдёте сквозь оболочку фреймворков: от принципов агентов, архитектуры и классических парадигм — до собственных мультиагентных приложений. Лучший способ учиться — практика. Надеемся, курс станет точкой входа в мир агентов и поможет превратиться из «пользователя» LLM в «строителя» агентных систем.

> **Локальная русская редакция:** ядро курса (главы, предисловие, код) и приоритетные Extra (собеседования, контекст, Skills, FAQ, грабли, self-evolution) — на русском. Extra03/06/07/11–13, Additional-Chapter и Co-creation-projects не переводились (см. [`RU_LOCALIZATION.md`](./RU_LOCALIZATION.md)).

## Быстрый старт

### Онлайн-чтение (оригинал)
**[Международный доступ](https://datawhalechina.github.io/hello-agents/)** | **[Ускорение в Китае](https://hello-agents.datawhale.cc)**

### Локальное чтение
Откройте [`docs/index.html`](./docs/index.html) через Docsify или читайте markdown в `docs/`.

### Что вы получите

- **Бесплатный open source Datawhale** — весь контент проекта бесплатно
- **Принципы** — понятия, история и классические парадигмы агентов
- **Практика** — low-code платформы и кодовые фреймворки агентов
- **Свой фреймворк [HelloAgents](https://github.com/jjyaoao/helloagents)** — с нуля на OpenAI-совместимом API
- **Продвинутые навыки** — инженерия контекста, Memory, протоколы, оценка
- **Обучение моделей** — Agentic RL, от SFT до GRPO
- **Кейсы** — умный помощник путешественника, кибер-городок и др.
- **Собеседования** — вопросы и опорные ответы в Extra-Chapter

## Навигация по содержанию

| Глава | Содержание | Статус |
| ----- | ---------- | ------ |
| [Предисловие](./docs/Preface.md) | Происхождение проекта, фон, советы читателю | ✅ |
| **Часть I: Основы агентов и языковых моделей** | | |
| [Глава 1. Знакомство с агентами](./docs/chapter1/Chapter1-Introduction-to-Agents.md) | Определение, типы, парадигмы, применения | ✅ |
| [Глава 2. История агентов](./docs/chapter2/Chapter2-History-of-Agents.md) | От символизма к LLM-агентам | ✅ |
| [Глава 3. Основы больших языковых моделей](./docs/chapter3/Chapter3-Fundamentals-of-Large-Language-Models.md) | Transformer, промпты, LLM и их ограничения | ✅ |
| **Часть II: Создаём своего LLM-агента** | | |
| [Глава 4. Классические парадигмы агентов](./docs/chapter4/Chapter4-Building-Classic-Agent-Paradigms.md) | ReAct, Plan-and-Solve, Reflection | ✅ |
| [Глава 5. Агенты на low-code платформах](./docs/chapter5/Chapter5-Building-Agents-with-Low-Code-Platforms.md) | Coze, Dify, n8n | ✅ |
| [Глава 6. Практика работы с фреймворками](./docs/chapter6/Chapter6-Framework-Development-Practice.md) | AutoGen, AgentScope, LangGraph | ✅ |
| [Глава 7. Свой фреймворк агента](./docs/chapter7/Chapter7-Building-Your-Agent-Framework.md) | Фреймворк с нуля | ✅ |
| **Часть III: Продвинутые темы** | | |
| [Глава 8. Память и поиск](./docs/chapter8/Chapter8-Memory-and-Retrieval.md) | Память, RAG, хранение | ✅ |
| [Глава 9. Инженерия контекста](./docs/chapter9/Chapter9-Context-Engineering.md) | Контекст для непрерывного взаимодействия | ✅ |
| [Глава 10. Протоколы общения агентов](./docs/chapter10/Chapter10-Agent-Communication-Protocols.md) | MCP, A2A, ANP | ✅ |
| [Глава 11. Agentic-RL](./docs/chapter11/Chapter11-Agentic-RL.md) | Обучение LLM от SFT до GRPO | ✅ |
| [Глава 12. Оценка производительности агентов](./docs/chapter12/Chapter12-Agent-Performance-Evaluation.md) | Метрики, бенчмарки, фреймворки оценки | ✅ |
| **Часть IV: Комплексные кейсы** | | |
| [Глава 13. Умный помощник путешественника](./docs/chapter13/Chapter13-Intelligent-Travel-Assistant.md) | MCP и мультиагентное сотрудничество | ✅ |
| [Глава 14. Агент автоматизированного глубокого исследования](./docs/chapter14/Chapter14-Automated-Deep-Research-Agent.md) | DeepResearch Agent | ✅ |
| [Глава 15. Кибер-городок](./docs/chapter15/Chapter15-Building-Cyber-Town.md) | Агенты и игры, социальная динамика | ✅ |
| **Часть V: Выпускной проект и перспективы** | | |
| [Глава 16. Выпускной проект](./docs/chapter16/Chapter16-Graduation-Project.md) | Своё полное мультиагентное приложение | ✅ |

### Сообщество и Extra

| Материал | Кратко |
| -------- | ------ |
| [00 — Совместные выпускные проекты](https://github.com/datawhalechina/hello-agents/blob/main/Co-creation-projects) | Co-creation (без перевода) |
| [01 — Вопросы на собеседования](./Extra-Chapter/Extra01-Interview-Questions.md) | Интервью (RU) |
| [01 — Опорные ответы](./Extra-Chapter/Extra01-Reference-Answers.md) | Ответы к собеседованиям (RU) |
| [02 — Инженерия контекста](./Extra-Chapter/Extra02-Context-Engineering-Supplement.md) | Дополнение к гл. 9 (RU) |
| [04 — FAQ](./Extra-Chapter/Extra04-Datawhale-FAQ.md) | FAQ курса (RU) |
| [05 — Agent Skills](./Extra-Chapter/Extra05-Agent-Skills.md) | Skills и MCP (RU) |
| [08 — Как писать Skill](./Extra-Chapter/Extra08-How-to-Write-Good-Skills.md) | Практика Skills (RU) |
| [09 — Грабли разработки](./Extra-Chapter/Extra09-Agent-Dev-Pitfalls-and-Lessons.md) | Уроки Code Agent (RU) |
| [10 — Self-evolution](./Extra-Chapter/Extra10-Agent-Self-Evolution.md) | Самоэволюция агентов (RU) |
| [Extra-Chapter](./Extra-Chapter/) | Полный список, в т.ч. непереведённые CN |

### PDF

> Hello-Agents PDF: https://github.com/datawhalechina/hello-agents/releases/latest/  
> Скачивание в Китае: https://www.datawhale.cn/learn/summary/239

## Как учиться

Курс подходит **разработчикам ИИ, инженерам, студентам** с базой программирования и **самоучкам**, интересующимся агентами. Нужны базовый Python и понимание, как вызывать LLM по API. Глубокий бэкграунд в алгоритмах и обучении моделей не обязателен.

- **Часть I (гл. 1–3)** — определение, типы и история агентов; основы LLM  
- **Часть II (гл. 4–7)** — ReAct и классика, low-code, фреймворки, свой HelloAgents  
- **Часть III (гл. 8–12)** — память, контекст, протоколы, обучение, оценка  
- **Часть IV (гл. 13–15)** — комплексные проекты  
- **Часть V (гл. 16)** — выпускной проект и взгляд вперёд  

Код — в папке `code`. Сочетайте теорию с практикой: запускайте и меняйте примеры.

## Как внести вклад

Оригинальный upstream — open-source сообщество Datawhale. Баги, идеи и PR — в [GitHub Hello-Agents](https://github.com/datawhalechina/Hello-Agents).

## Благодарности

### Основные авторы
- [Chen Sizhou — лид проекта](https://github.com/jjyaoao) (Datawhale)
- [Sun Tao](https://github.com/fengju0213) (Datawhale, CAMEL-AI, гл. 9)
- [Jiang Shufan](https://github.com/Tsumugii24) (Datawhale)
- [Huang Peilin](https://github.com/HeteroCat) (гл. 5)
- [Zeng Xinmin](https://github.com/fancyboi999) (гл. 14)
- [Hu Hao](https://github.com/ACGpp) (Datawhale)
- [Zhu Xinzhong](https://xinzhongzhu.github.io/) (Datawhale)

Особая благодарность [@Sm1les](https://github.com/Sm1les) и всем контрибьюторам.

## Цитирование

```bibtex
@misc{hello_agents2025,
  title  = {Hello-Agents: Building an AI Agent from Scratch},
  author = {Sizhou Chen and Tao Sun and Shufan Jiang and Peilin Huang and Xinmin Zeng and Hao Hu and Xinzhong Zhu and all Hello-Agents contributors},
  year   = {2025},
  url    = {https://github.com/datawhalechina/Hello-Agents},
  note   = {GitHub repository}
}
```

## Лицензия

Работа распространяется на условиях [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](http://creativecommons.org/licenses/by-nc-sa/4.0/).
