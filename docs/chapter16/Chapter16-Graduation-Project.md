# Глава 16. Выпускной проект

Поздравляем с достижением последней главы руководства Hello-Agents! В предыдущих 15 главах мы создали платформу HelloAgents с нуля и узнали об основных концепциях агентов, нескольких парадигмах, системах инструментов, механизмах памяти, протоколах связи, обучении с подкреплением и оценке производительности. В главах 13–15 мы также продемонстрировали, как интегрировать все полученные знания с помощью трех полных практических проектов («Интеллектуальный помощник в путешествии», «Автоматический агент глубоких исследований» и «Кибергород»).

Теперь пришло время стать настоящим строителем агентских систем! Эта глава поможет вам **создать собственное многоагентное приложение** и поделиться своими достижениями с сообществом посредством совместной работы с открытым исходным кодом.

## 16.1 Значение дипломного проекта

### 16.1.1 Зачем делать дипломный проект

Лучший способ изучить технологию — это не чтение обучающих программ, а **практическая практика**. Изучая предыдущие главы, вы овладели теоретическими знаниями и техническими инструментами для построения агентных систем. Однако настоящая проблема заключается в следующем: **Как применить эти знания к реальным проблемам? Как спроектировать полноценную систему? Как обрабатывать различные крайние случаи и исключения?**

Основная ценность дипломного проекта — развить ваши комплексные прикладные способности, выборочно интегрируя все полученные ранее знания (парадигмы агентов, системы инструментов, механизмы памяти, протоколы связи и т. д.) в законченный проект.

Мы надеемся, что благодаря изучению и практике, описанным в этой главе, вы сможете самостоятельно спроектировать и реализовать полноценное приложение-агент, умело использовать различные функции платформы HelloAgents, освоить базовые операции Git и GitHub, научиться писать понятную проектную документацию, участвовать в совместной разработке сообщества с открытым исходным кодом и, в конечном итоге, получить техническую работу, которую вы сможете продемонстрировать.

### 16.1.2 Форма дипломного проекта

Ваш дипломный проект будет отправлен в репозиторий проектов совместного творчества Hello-Agents (`Co-creation-projects`каталог) в виде **проекта с открытым исходным кодом**. Конкретные требования заключаются в следующем:

1. **Именование проекта**: используйте формат `{your-GitHub-username}-{project-name}`, например `jjyaoao-CodeReviewAgent`

2. **Содержание проекта**:
   - Запускаемый блокнот Jupyter (файл .ipynb) или скрипт Python.
   - Полный список зависимостей (requirements.txt)
   - Очистить документацию README (`README.md`)
   - Дополнительно: демонстрационные видеоролики, снимки экрана, наборы данных и т. д.

3. **Метод отправки**: Отправка через запрос на извлечение GitHub (PR).

4. **Процесс проверки**. Члены сообщества проверят ваш код, предоставят предложения по улучшению и после утверждения объединят его в основной репозиторий.

## 16.2 Руководство по выбору темы проекта

### 16.2.1 Принципы выбора тем

Хороший дипломный проект должен быть практичным, решать реальные проблемы, а не технологии ради технологий. Нам необходимо добиться завершения в течение ограниченного времени и ресурсов, четко демонстрируя при этом ваши технические возможности.

### 16.2.2 Рекомендуемые направления тем

Вот несколько рекомендуемых направлений проекта – вы можете выбрать одно или предложить свои идеи:

**(1) Инструменты повышения производительности**

- **Интеллектуальный помощник по проверке кода**: автоматически анализируйте качество кода, обнаруживайте потенциальные ошибки и предоставляйте предложения по оптимизации.
- **Интеллектуальный генератор документации**: автоматически создавайте документацию по API и руководства пользователя на основе кода.
- **Интеллектуальный помощник по собраниям**: записывайте содержимое собрания, генерируйте протоколы собраний, извлекайте элементы действий.
- **Интеллектуальный помощник по электронной почте**: автоматически классифицируйте электронные письма, создавайте черновики ответов, напоминайте о важных делах.

**(2) Помощь в обучении**

- **Интеллектуальный партнер по обучению**: рекомендуйте учебные ресурсы на основе прогресса в обучении, создавайте практические вопросы, отвечайте на вопросы.
- **Интеллектуальный помощник по работе с бумагами**: помогает находить литературу, обобщать статьи, генерировать цитаты.
- **Репетитор по интеллектуальному программированию**: предоставляет упражнения по программированию, проверку кода, планирование пути обучения.
- **Интеллектуальный помощник по изучению языка**: обеспечивает разговорную практику, коррекцию грамматики, расширение словарного запаса.

**(3) Творческие развлечения**

- **Интеллектуальный генератор историй**: создавайте романы, сценарии и стихи на основе данных пользователя.
- **Умный игровой NPC**: создавайте индивидуальных игровых персонажей, которые смогут естественно общаться с игроками.
- **Интеллектуальная рекомендация музыки**: рекомендуйте музыку в зависимости от настроения и сцены, создавайте плейлисты.
- **Интеллектуальный помощник по рецептам**: рекомендуйте рецепты на основе ингредиентов и вкуса, создавайте списки покупок.

**(4) Анализ данных**

- **Интеллектуальный аналитик данных**: автоматически анализируйте данные, создавайте диаграммы визуализации, записывайте аналитические отчеты.
- **Интеллектуальный анализ акций**: анализируйте биржевые данные и настроения в новостях, предоставляйте советы по инвестированию.
- **Интеллектуальный мониторинг общественного мнения**: отслеживайте социальные сети и новостные сайты, анализируйте тенденции общественного мнения.
- **Интеллектуальный конкурентный анализ**: сбор информации о конкурентах, сравнительный анализ, создание отчетов.

**(5) Службы жизнеобеспечения**

- **Интеллектуальный помощник по здоровью**: записывайте данные о состоянии здоровья, предоставляйте советы по здоровью, создавайте планы тренировок.
- **Интеллектуальный финансовый помощник**: записывайте доходы и расходы, анализируйте привычки расходов, предоставляйте финансовые советы.
- **Интеллектуальный помощник для покупок**: сравнивайте цены, рекомендуйте товары, создавайте списки покупок.
- **Интеллектуальное управление домом**: управляйте устройствами умного дома с помощью естественного языка.

### 16.2.3 Пример выбора темы

Проиллюстрируем, как выбрать тему и разработать проект на конкретном примере.

**Название проекта**: Интеллектуальный помощник по проверке кода (CodeReviewAgent)

**Анализ проблем**. Проверка кода — важная часть разработки программного обеспечения, но проверка вручную требует много времени и может привести к упущению проблем. Существующие инструменты статического анализа могут только находить синтаксические ошибки и не могут понять логику кода, поэтому необходим интеллектуальный помощник, который сможет понять семантику кода и обеспечить углубленный анализ.

**Основные функции**. В этом проекте будет реализован анализ качества кода (проверка стиля кода, соглашения об именах, полнота комментариев), обнаружение потенциальных ошибок (обнаружение логических ошибок, проблем с граничными условиями, утечки ресурсов), предложения по оптимизации производительности (выявление узких мест в производительности, предложение решений по оптимизации), сканирование уязвимостей безопасности (обнаружение SQL-инъекций, XSS и других проблем безопасности) и рекомендации по передовому опыту (предложение улучшений на основе особенностей языка и шаблонов проектирования).

**Ожидаемые результаты**. Конечным результатом станет работающий Jupyter Notebook, демонстрирующий полный процесс проверки, поддерживающий основные языки, такие как Python и JavaScript, способный генерировать структурированные отчеты о проверке в формате Markdown, а также предоставляющий конкретные примеры кода и предложения по улучшению.

## 16.3 Подготовка среды разработки

### 16.3.1 Установка необходимых инструментов

Прежде чем приступить к разработке, убедитесь, что в вашей среде разработки установлены следующие инструменты:

**(1) Среда Python**

```bash
# Install HelloAgents
pip install "hello-agents[all]"
```

**(2) Git и GitHub**

```bash
# Check Git version
git --version

# Configure Git user information
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Configure GitHub SSH key (recommended)
# 1. Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# 2. Add public key to GitHub
# Copy the content of ~/.ssh/id_ed25519.pub
# Add in GitHub Settings > SSH and GPG keys

# 3. Test connection
ssh -T git@github.com
```

**(3) Блокнот Jupyter**

```bash
# Install Jupyter
pip install jupyter notebook

# Or use JupyterLab (recommended)
pip install jupyterlab

# Start Jupyter
jupyter lab
```

### 16.3.2 Форк репозитория проекта

**Шаг 1. Создайте форк репозитория**

1. Посетите репозиторий Hello-Agents: https://github.com/datawhalechina/hello-agents.
2. Нажмите кнопку «Вилка» в правом верхнем углу, как показано в красном поле на рисунке 16.1.
3. Выберите свою учетную запись GitHub и создайте форк.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/hello-agents/main/docs/images/16-figures/16-1.png" alt="" width="85%"/>
  <p>Рисунок 16.1. Шаги создания форка репозитория</p>
</div>

**Шаг 2. Клонируйте в локальное хранилище**

```bash
# As shown in Рис. 16.2, clone your forked repository
git clone git@github.com:your-username/hello-agents.git

# Enter project directory
cd Hello-Agents

# Add upstream repository (for syncing updates)
git remote add upstream https://github.com/datawhalechina/hello-agents.git

# View remote repositories
git remote -v
```

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/hello-agents/main/docs/images/16-figures/16-2.png" alt="" width="85%"/>
  <p>Рисунок 16.2 Клонирование репозитория в локальный</p>
</div>

**Шаг 3. Создайте ветку разработки**

```bash
# Create and switch to new branch
git checkout -b feature/your-project-name

# For example:
git checkout -b feature/code-review-agent
```

### 16.3.3 Структура каталога проекта

Создайте папку проекта в папке`Co-creation-projects`каталог:

```bash
# Enter co-creation projects directory
cd Co-creation-projects

# Create project folder (format: GitHub-username-project-name)
mkdir your-username-project-name

# For example:
mkdir jjyaoao-CodeReviewAgent

# Enter project directory
cd jjyaoao-CodeReviewAgent
```

Рекомендуемая структура проекта:

```
jjyaoao-CodeReviewAgent/
├── README.md              # Project documentation
├── requirements.txt       # Python dependency list
├── main.ipynb            # Main Jupyter Notebook
├── data/                 # Data files (optional)
│   ├── sample_code.py
│   └── test_cases.json
├── outputs/              # Output results (optional)
│   ├── review_report.md
│   └── screenshots/
├── src/                  # Source code (optional, if code is extensive)
│   ├── agents/
│   ├── tools/
│   └── utils/
└── .env.example          # Environment variable template
```

## 16.4 Руководство по разработке проекта

### 16.4.1 Написание документации README

README — лицо вашего проекта. Хороший README должен содержать следующее:

```markdown
# Project Name

> One-sentence description of your project

## 📝 Project Introduction

Detailed introduction to your project:
- What problem does it solve?
- What are its special features?
- What scenarios is it suitable for?

## ✨ Core Features

- [ ] Feature 1: Description
- [ ] Feature 2: Description
- [ ] Feature 3: Description

## 🛠️ Technology Stack

- HelloAgents framework
- Agent paradigms used (e.g., ReAct, Plan-and-Solve, etc.)
- Tools and APIs used
- Other dependency libraries

## 🚀 Quick Start

### Environment Requirements

- Python 3.10+
- Other requirements

### Install Dependencies


pip install -r requirements.txt


### Configure API Keys


# Create .env file
cp .env.example .env

# Edit .env file and fill in your API keys


### Run Project


# Start Jupyter Notebook
jupyter lab

# Open main.ipynb and run


## 📖 Usage Examples

Show how to use your project, preferably with code examples and results.

## 🎯 Project Highlights

- Highlight 1: Explanation
- Highlight 2: Explanation
- Highlight 3: Explanation

## 📊 Performance Evaluation

If you have evaluation results, display them here:
- Accuracy: XX%
- Response time: XX seconds
- Other metrics

## 🔮 Future Plans

- [ ] Feature 1 to be implemented
- [ ] Feature 2 to be implemented
- [ ] Parts to be optimized

## 🤝 Contribution Guidelines

Issues and Pull Requests are welcome!

## 📄 License

MIT License

## 👤 Author

- GitHub: [@your-username](https://github.com/your-username)
- Email: your.email@example.com (optional)

## 🙏 Acknowledgments

Thanks to the Datawhale community and Hello-Agents project!
```

### 16.4.2 Написание файла require.txt

Перечислите все зависимости Python, необходимые для проекта:

```txt
# Core dependencies
hello-agents[all]>=0.2.7

# Visualization (if needed)
matplotlib>=3.7.0
plotly>=5.14.0

# Web framework (if needed)
fastapi>=0.109.0
uvicorn>=0.27.0
```

### 16.4.3 Разработка блокнота Jupyter

**(1) Рекомендации по структуре ноутбука**

Хороший блокнот Jupyter должен содержать следующие части:

```python
# ========================================
# Part 1: Project Introduction
# ========================================

"""
# Project Name

## Project Introduction
Brief introduction to project goals and features

## Author Information
- Name: XXX
- GitHub: @XXX
- Date: 2025-XX-XX
"""

# ========================================
# Part 2: Environment Configuration
# ========================================

# Install dependencies
!pip install -q hello-agents[all]

# Import necessary libraries
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import BaseTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ========================================
# Part 3: Tool Definition
# ========================================

class CustomTool(BaseTool):
    """Custom tool class"""

    name = "tool_name"
    description = "Tool description"

    def run(self, query: str) -> str:
        """Tool execution logic"""
        # Implement your tool logic
        return "Result"

# ========================================
# Part 4: Agent Construction
# ========================================

# Create LLM
llm = HelloAgentsLLM()

# Create agent
agent = SimpleAgent(
    name="Agent Name",
    llm=llm,
    system_prompt="System prompt"
)

# Add tools
agent.add_tool(CustomTool())

# ========================================
# Part 5: Feature Demonstration
# ========================================

# Example 1: Basic functionality
print("=== Example 1: Basic Functionality ===")
result = agent.run("User input")
print(result)

# Example 2: Complex scenario
print("\n=== Example 2: Complex Scenario ===")
result = agent.run("Complex user input")
print(result)

# ========================================
# Part 6: Performance Evaluation (Optional)
# ========================================

# Evaluation code
# ...

# ========================================
# Part 7: Summary and Outlook
# ========================================

"""
## Project Summary

### Implemented Features
- Feature 1
- Feature 2

### Challenges Encountered
- Challenge 1 and solution
- Challenge 2 and solution

### Future Improvement Directions
- Improvement 1
- Improvement 2
"""
```

### 16.4.4 Тестирование вашего проекта

Перед отправкой воспользуйтесь этим контрольным списком, чтобы определить, соответствует ли ваш проект требованиям подачи:

```markdown
- [ ] Code runs normally without errors
- [ ] README documentation is complete with clear instructions
- [ ] requirements.txt contains all dependencies
- [ ] Clear usage examples provided
- [ ] Code has appropriate comments
- [ ] Output results meet expectations
- [ ] Common exception cases handled
- [ ] Project structure is clear with standardized file naming
- [ ] Large files properly handled (see next section)
```

### 16.4.5 Руководство по работе с большими файлами

**⚠️ Важно: избегайте слишком большого размера основного репозитория**

Чтобы сохранить легкость основного репозитория Hello-Agents, следуйте этим рекомендациям по обработке больших файлов:

**(1) Ограничения на размер файла**

- **Общий размер проекта**: не более 5 МБ.
- **Прямая отправка запрещена**: видеофайлы, большие наборы данных, файлы моделей.

**(2) Решения для обработки больших файлов**

Если ваш проект содержит большие файлы (наборы данных, видео, модели и т. д.), воспользуйтесь следующими решениями:

**Решение 1. Используйте внешние ссылки (рекомендуется)**

Загрузите большие файлы на внешние платформы и предоставьте ссылки для скачивания в README:

```markdown
## Datasets

The datasets used in this project are large. Please download from the following links:

- Dataset 1: [Baidu Netdisk](link) Extraction code: xxxx
- Dataset 2: [Google Drive](link)
- Demo video: [Bilibili](link) / [YouTube](link)
```

Рекомендуемые внешние платформы:
- **Наборы данных**: Baidu Netdisk, Google Drive, Kaggle, наборы данных HuggingFace.
- **Видео**: Bilibili, YouTube, Tencent Video.
- **Модели**: модели HuggingFace, ModelScope.
- **Изображения**: проблемы с GitHub, услуги хостинга изображений.

**Решение 2. Создайте независимый репозиторий**

Если в проекте много ресурсов, рассмотрите возможность создания независимого хранилища данных:

```markdown
## Project Resources

Due to the large amount of data and demo resources, a separate resource repository has been created:

- Resource repository: https://github.com/your-username/project-name-resources
- Contains: Datasets, demo videos, model files, test data, etc.

### Usage

\`\`\`bash
# Clone resource repository
git clone https://github.com/your-username/project-name-resources.git

# Copy data to project directory
cp -r project-name-resources/data ./data
\`\`\`
```

**Решение 3. Используйте образцы данных**

В основном репозитории предоставляйте только небольшие образцы данных:

```python
# Explain in README
## Data Description

- `data/sample.csv`: Sample data (100 records)
- Complete dataset (100,000 records) download from [here](link)
```

**(3) Пример передового опыта**

```
your-username-project-name/
├── README.md              # Contains external resource links
├── requirements.txt
├── main.ipynb
├── .gitignore            # Ignore large files
├── data/
│   └── sample.csv        # Sample data only (<1MB)
└── outputs/
    └── demo_result.png   # Demo results only (<1MB)
```

Объяснение README:

```markdown
## Data and Resources

### Sample Data
Project includes small-scale sample data for quick testing (located in `data/sample.csv`)

### Complete Dataset
Complete dataset (500MB) download from the following link:
- Baidu Netdisk: [Link] Extraction code: xxxx
- Extract to `data/` directory after download

### Demo Video
- Bilibili: [Project Demo Video](link)
- YouTube: [Demo Video](link)
```

## 16.5 Отправка запроса на включение

### 16.5.1 Отправка кода на GitHub

**Шаг 1. Проверьте изменения**

```bash
# View modified files
git status
```

**Шаг 2. Добавьте файлы**

```bash
# Add all modified files
git add .

# Or add specific files
git add Co-creation-projects/your-username-project-name/
```

**Шаг 3. Зафиксируйте изменения**

Сообщения о фиксации должны иметь следующий формат:

```bash
# Format: type: brief description
git commit -m "feat: Add XXX graduation project"
```

**Спецификации типа фиксации:**

- `feat`: новая функция или проект (используйте этот тип для дипломных проектов).
- `fix`: исправление ошибки.
- `docs`: обновление документации.
- `style`: настройка формата кода (не влияет на функциональность)
- `refactor`: рефакторинг кода.
- `test`: связанный с тестированием
- `chore`: другие модификации (например, обновления зависимостей).

**Шаг 4. Отправьте сообщение на GitHub**

```bash
# Push to your forked repository
git push origin feature/your-project-name
```

### 16.5.2 Создание запроса на включение

**Шаг 1. Посетите GitHub**

1. Посетите свой раздвоенный репозиторий: https://github.com/your-username/hello-agents.
2. Перейдите на вкладку «Запросы на включение», как показано на рисунке 16.3.
3. Нажмите кнопку «Новый запрос на включение»

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/hello-agents/main/docs/images/16-figures/16-3.png" alt="" width="85%"/>
  <p>Рисунок 16.3 Создание запроса на включение</p>
</div>

**Шаг 2. Выберите ветки**

- Базовый репозиторий: `datawhalechina/hello-agents`
- Базовая ветка: `main`
- Головной репозиторий: `ваше-пользователь/привет-агенты`
- Ветка сравнения: `feature/имя-вашего-проекта`

**Шаг 3. Заполните PR-информацию**

**⚠️ Важно: Единый формат заголовка PR**

Для удобства управления и поиска все PR-заголовки дипломных проектов должны иметь следующий формат:

```
[Graduation Project] Project Name - Brief Description
```

Примеры:
-`[Graduation Project] CodeReviewAgent - Intelligent Code Review Assistant`
- `[Graduation Project] StudyBuddy - AI Learning Partner`
- `[Graduation Project] DataAnalyst - Intelligent Data Analyst`

**Шаблон PR-описания:**

```markdown
## Project Information

- **Project Name**: XXX
- **Author**: @your-username
- **Project Type**: Productivity Tool/Learning Assistance/Creative Entertainment/Data Analysis/Life Service

## Project Introduction

Brief description of your project (2-3 sentences)

## Core Features

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

## Technical Highlights

- Used XXX paradigm
- Implemented XXX functionality
- Optimized XXX performance

## Demo Effects

(Optional) Add screenshots or GIFs to showcase project effects

## Self-Check List

- [ ] Code runs normally
- [ ] README documentation complete
- [ ] requirements.txt complete
- [ ] Clear usage examples provided
- [ ] Code has appropriate comments

## Other Notes

(Optional) Other content that needs explanation
```

**Шаг 4. Отправьте заявку**

Как показано на рисунке 16.4, нажмите кнопку «Создать запрос на включение», чтобы отправить запрос.

<div align="center">
  <img src="https://raw.githubusercontent.com/datawhalechina/hello-agents/main/docs/images/16-figures/16-4.png" alt="" width="85%"/>
  <p>Рисунок 16.4. Отправка запроса на включение</p>
</div>

### 16.5.3 Ответ на комментарии к обзору

После отправки PR члены сообщества рассмотрят ваш код и дадут предложения. Пожалуйста, ответьте срочно:

1. **Просмотр комментариев**: просмотрите комментарии рецензентов на странице PR.
2. **Изменить код**: изменить код на основе предложений.
3. **Отправить обновления**:
   ```bash
   git add .
   git commit -m "fix: Modify XXX based on review comments"
   git push origin feature/your-project-name
   ```
4. **Ответ на комментарии**: ответ рецензентам на GitHub с объяснением внесенных вами изменений.

## 16.6 Пример демонстрации проекта

Чтобы помочь вам лучше понять требования дипломного проекта, вот полный пример проекта. Не волнуйтесь, небольшие творческие идеи также могут быть включены. Любая работа, которую вы создаете сами, достойна уважения.

**Информация о проекте**

- **Название проекта**: CodeReviewAgent
- **Автор**: @jjyaoao
- **Путь к проекту**: `Co-creation-projects/jjyaoao-CodeReviewAgent/`

**Структура проекта**

```
jjyaoao-CodeReviewAgent/
├── README.md              # Project documentation
├── requirements.txt       # Dependency list
├── main.ipynb            # Main program (includes quick demo and full features)
├── .env.example          # Environment variable example
├── .gitignore            # Git ignore rules
├── data/
│   └── sample_code.py    # Sample code
└── outputs/
    └── review_report.md  # Sample report
```

**Фрагмент основного кода (main.ipynb)**

```python
# ========================================
# Intelligent Code Review Assistant
# ========================================

from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import Tool, ToolParameter
from typing import Dict, Any, List
import ast
import os

# ========================================
# 0. Configure LLM Parameters
# ========================================

os.environ["LLM_MODEL_ID"] = "Qwen/Qwen2.5-72B-Instruct"
os.environ["LLM_API_KEY"] = "your_api_key_here"
os.environ["LLM_BASE_URL"] = "https://api-inference.modelscope.cn/v1/"
os.environ["LLM_TIMEOUT"] = "60"

# ========================================
# 1. Define Code Analysis Tools
# ========================================

class CodeAnalysisTool(Tool):
    """Code static analysis tool"""

    def __init__(self):
        super().__init__(
            name="code_analysis",
            description="Analyze Python code structure, complexity, and potential issues"
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        """Analyze code and return results"""
        code = parameters.get("code", "")
        if not code:
            return "Error: Code cannot be empty"

        try:
            tree = ast.parse(code)
            functions = [node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree)
                      if isinstance(node, ast.ClassDef)]

            result = {
                "Number of functions": len(functions),
                "Number of classes": len(classes),
                "Lines of code": len(code.split('\n')),
                "Function list": [f.name for f in functions],
                "Class list": [c.name for c in classes]
            }
            return str(result)
        except SyntaxError as e:
            return f"Syntax error: {str(e)}"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="Python code to analyze",
                required=True
            )
        ]

class StyleCheckTool(Tool):
    """Code style checking tool"""

    def __init__(self):
        super().__init__(
            name="style_check",
            description="Check if code complies with PEP 8 standards"
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        """Check code style"""
        code = parameters.get("code", "")
        if not code:
            return "Error: Code cannot be empty"

        issues = []
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 79:
                issues.append(f"Line {i}: Exceeds 79 characters")
            if line.startswith(' ') and not line.startswith('    '):
                if len(line) - len(line.lstrip()) not in [0, 4, 8, 12]:
                    issues.append(f"Line {i}: Non-standard indentation")

        if not issues:
            return "Code style is good, complies with PEP 8 standards"
        return "Found the following issues:\n" + "\n".join(issues)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="Python code to check",
                required=True
            )
        ]

# ========================================
# 2. Create Tool Registry and Agent
# ========================================

# Create tool registry
tool_registry = ToolRegistry()
tool_registry.register_tool(CodeAnalysisTool())
tool_registry.register_tool(StyleCheckTool())

# Initialize LLM
llm = HelloAgentsLLM()

# Define system prompt
system_prompt = """You are an experienced code review expert. Your tasks are:

1. Use code_analysis tool to analyze code structure
2. Use style_check tool to check code style
3. Based on analysis results, provide detailed review report

The review report should include:
- Code structure analysis
- Style issues
- Potential bugs
- Performance optimization suggestions
- Best practice recommendations

Please output the report in Markdown format."""

# Create agent
agent = SimpleAgent(
    name="Code Review Assistant",
    llm=llm,
    system_prompt=system_prompt,
    tool_registry=tool_registry
)

# ========================================
# 3. Run Example
# ========================================

# Read sample code
with open("data/sample_code.py", "r", encoding="utf-8") as f:
    sample_code = f.read()

print("=== Code to Review ===")
print(sample_code)
print("\n" + "="*50 + "\n")

# Execute code review
print("=== Starting Code Review ===")
review_result = agent.run(f"Please review the following Python code:\n\n```python\n{sample_code}\n```")

print(review_result)

# Save review report
with open("outputs/review_report.md", "w", encoding="utf-8") as f:
    f.write(review_result)

print("\nReview report saved to outputs/review_report.md")
```

**Пример README.md**

```markdown
# CodeReviewAgent - Intelligent Code Review Assistant

> Intelligent code review tool based on HelloAgents framework

## 📝 Project Introduction

CodeReviewAgent is an intelligent code review assistant that can automatically analyze Python code quality, discover potential issues, and provide optimization suggestions.

### Core Features

- ✅ Code structure analysis: Count functions, classes, lines of code, etc.
- ✅ Style checking: Check compliance with PEP 8 standards
- ✅ Intelligent suggestions: Provide in-depth analysis and optimization suggestions based on LLM
- ✅ Report generation: Generate review reports in Markdown format

## 🛠️ Technology Stack

- HelloAgents framework (SimpleAgent + ToolRegistry)
- Python AST module (code parsing)
- ModelScope API (Qwen2.5-72B model)

## 🚀 Quick Start

### Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### Configure LLM Parameters

**Method 1: Use .env file**

\`\`\`bash
cp .env.example .env
# Edit .env file and fill in your API key
\`\`\`

**Method 2: Set directly in Notebook**

The project is pre-configured with ModelScope API and can run directly. To modify, edit the configuration code in Part 1 of main.ipynb.

### Run Project

\`\`\`bash
jupyter lab
# Open main.ipynb and run all cells
\`\`\`

## 📖 Usage Example

1. Place code to review in `data/sample_code.py`
2. Run `main.ipynb`
3. View generated review report `outputs/review_report.md`

## 🎯 Project Highlights

- **Automation**: No need for manual line-by-line checking, automatically discovers issues
- **Intelligence**: Uses LLM to understand code semantics and provide in-depth suggestions
- **Extensibility**: Easy to add new checking rules and tools

## 👤 Author

- GitHub: [@jjyaoao](https://github.com/jjyaoao)
- Project link: [CodeReviewAgent](https://github.com/datawhalechina/hello-agents/tree/main/Co-creation-projects/jjyaoao-CodeReviewAgent)

## 🙏 Acknowledgments

Thanks to the Datawhale community and Hello-Agents project!
```

## 16.7 Резюме и перспективы

Выполнив дипломный проект, вы должны были освоить полный процесс проектирования системы агентов: проектирование архитектуры системы на основе требований, умелое использование различных функций и компонентов платформы HelloAgents, разработку пользовательских инструментов для расширения возможностей агента, завершение полной разработки проекта от анализа требований до реализации кода, обучение использованию Git и GitHub для совместной работы с открытым исходным кодом и написание понятной технической документации.

В этом проекте мы создали платформу HelloAgents с нуля и использовали ее для реализации множества практических приложений. Выполнение дипломного проекта – это только начало. Вы можете продолжать углублять изучение дополнительных парадигм и алгоритмов агентов, оперативного проектирования и контекстного проектирования, механизмов многоагентного сотрудничества и других теоретических знаний. Вы также можете расширить свой набор технологий, изучив веб-разработку для создания полноценных приложений, изучив базы данных для реализации постоянного хранения данных и научившись развертыванию для запуска приложений в Интернете. Вы также можете постоянно оптимизировать свой проект, добавляя дополнительные функции, оптимизируя производительность и удобство использования, а также улучшая тестирование и документацию. Что еще более важно, активно участвуйте в работе сообщества, помогая другим учащимся, участвуя в разработке платформы Hello-Agents и делясь своим опытом и знаниями.

От простого агента из главы 1 до возможности самостоятельно создавать полноценные мультиагентные приложения — вы прошли увлекательный путь обучения. Но это не конец – это новое начало.

Технология искусственного интеллекта быстро меняется, и область агентов полна безграничных возможностей. Мы надеемся, что вы сможете поддерживать любознательность и постоянно изучать новые технологии, смело использовать технологии искусственного интеллекта для решения практических проблем и создания ценности, охотно делиться своим опытом и достижениями с сообществом и постоянно совершенствовать свою работу в стремлении к совершенству.

Наконец, спасибо, что прочитали этот проект полностью. Мы надеемся, что вы получили что-то новое в процессе обучения и сможете применить полученные знания в реальных проектах, создавая удивительные агентные приложения. Будущее искусственного интеллекта полно безграничных возможностей — давайте исследовать и творить вместе!

**Помните: лучший способ обучения — это практическая практика!**

Теперь приступайте к созданию собственного приложения-агента! Будем рады видеть ваши отличные работы в каталоге Сотворчество-проекты!

Если проект Hello-Agents оказался для вас полезным, поставьте нам ⭐Звездочку!

---
<div align="center">
<strong>🎓 Поздравляем с завершением урока Hello-Agents! 🎉</strong>
</div>

