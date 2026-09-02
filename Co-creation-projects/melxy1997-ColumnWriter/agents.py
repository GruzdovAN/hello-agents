"""Основные агенты"""

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from hello_agents import (
    HelloAgentsLLM,
    ReActAgent,
    ReflectionAgent,
    PlanAndSolveAgent
)
from hello_agents.tools import MCPTool, ToolRegistry, SearchTool
from models import ColumnPlan, ReviewResult, ContentNode, ContentLevel
from prompts import get_structure_requirements, get_react_writer_prompt, get_reflection_writer_prompts, get_planner_prompts
from config import get_settings, get_word_count
from utils import JSONExtractor, parse_react_output, get_current_timestamp

settings = get_settings()

class LLMService:
    """Синглтон LLM-сервиса"""
    _instance: Optional[HelloAgentsLLM] = None
    
    @classmethod
    def get_llm(cls) -> HelloAgentsLLM:
        """Получить экземпляр LLM (паттерн синглтон)"""
        if cls._instance is None:
            cls._instance = HelloAgentsLLM()
            print(f"▸ LLM-сервис успешно инициализирован")
            print(f"   Провайдер: {cls._instance.provider}")
            print(f"   Модель: {cls._instance.model}")
        return cls._instance


class PlannerAgent:
    """
    Использует режим PlanAndSolveAgent.
    
    PlanAndSolveAgent разбивает задачу на подзадачи и выполняет их пошагово — идеально для планирования колонок:
    1. Анализ темы (понимание потребностей пользователя)
    2. Планирование подтем (декомпозиция задачи)
    3. Организация структуры (пошаговое выполнение)
    
    Поддерживает кэширование результатов планирования по ключу темы.
    """
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Инициализация агента планирования.
        
        Args:
            cache_dir: путь к каталогу кэша
        """
        self.llm = LLMService.get_llm()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Пользовательские промпты PlanAndSolve
        planner_prompts = {
            "planner": """
Вы — опытный эксперт по планированию колонок. Разбейте следующую тему колонки на чёткие шаги планирования подтем.

Тема: {question}

Выведите шаги планирования в формате:
```python
[
    "Шаг 1: проанализировать ключевые концепции темы и целевую аудиторию",
    "Шаг 2: определить общую структуру системы знаний",
    "Шаг 3: спланировать 2-4 подтемы с логической прогрессией",
    "Шаг 4: задать цели обучения и ключевые пункты для каждой подтемы",
    "Шаг 5: собрать полный план колонки"
]
```
Не более 10 шагов.

""",
            "executor": """
Вы — эксперт по выполнению планирования колонок. Выполняйте шаги плана и формируйте план колонки.

# Исходная тема: {question}
# Шаги плана: {plan}
# Выполненные шаги: {history}
# Текущий шаг: {current_step}

▸️ **Ключевые требования**:
- Не более 10 шагов.
- Если текущий шаг — «Шаг 5: собрать полный план колонки» или содержит слова «собрать», «полный», «план», **обязательно** выведите полный план колонки в формате JSON
- Если это не последний шаг, выведите результат анализа текущего шага (текстовый формат)

**Формат вывода на последнем шаге (только JSON, без другого текста)**:
```json
{{
  "column_title": "Общий заголовок колонки",
  "column_description": "Краткое описание колонки (100-200 слов)",
  "target_audience": "Целевая аудитория",
  "topics": [
    {{
      "id": "topic_001",
      "title": "Заголовок подтемы",
      "description": "Краткое описание подтемы (50-100 слов)",
      "estimated_words": 200,
      "key_points": ["пункт 1", "пункт 2", "пункт 3"],
      "prerequisites": ["предварительные знания 1", "предварительные знания 2"]
    }}
  ]
}}
```

**Важно**: на последнем шаге выводите только JSON, без префиксов вроде «результат анализа текущего шага».

Выполните текущий шаг:
"""
        }
        
        # Обёртка Executor с кэшированием
        from hello_agents.agents.plan_solve_agent import Executor
        
        class CachedExecutor(Executor):
            """Executor с кэшированием результатов каждого шага"""
            def __init__(self, llm_client, prompt_template, cache_dir, main_topic):
                super().__init__(llm_client, prompt_template)
                self.cache_dir = cache_dir
                self.main_topic = main_topic
                self.steps_cache_dir = cache_dir / "steps_cache"
                self.steps_cache_dir.mkdir(exist_ok=True)
            
            def _get_step_cache_key(self, step_index: int, step_content: str) -> Path:
                """Сформировать путь к файлу кэша шага"""
                # Ключ: тема + индекс шага + хэш содержимого шага
                step_hash = hashlib.md5(
                    f"{self.main_topic}_{step_index}_{step_content}".encode('utf-8')
                ).hexdigest()
                return self.steps_cache_dir / f"step_{step_index}_{step_hash}.json"
            
            def _load_step_from_cache(self, step_index: int, step_content: str) -> Optional[str]:
                """Загрузить результат шага из кэша"""
                cache_file = self._get_step_cache_key(step_index, step_content)
                if not cache_file.exists():
                    return None
                
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    # Проверить соответствие темы и шага в кэше
                    if (cache_data.get('topic') == self.main_topic and 
                        cache_data.get('step_index') == step_index and
                        cache_data.get('step_content') == step_content):
                        print(f"   ▸ Загружен результат шага {step_index} из кэша")
                        return cache_data.get('result')
                except Exception as e:
                    print(f"   ▸️  Ошибка загрузки кэша шага: {e}")
                return None
            
            def _save_step_to_cache(self, step_index: int, step_content: str, result: str):
                """Сохранить результат шага в кэш"""
                cache_file = self._get_step_cache_key(step_index, step_content)
                try:
                    cache_data = {
                        'topic': self.main_topic,
                        'step_index': step_index,
                        'step_content': step_content,
                        'result': result
                    }
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"   ▸️  Ошибка сохранения кэша шага: {e}")
            
            def execute(self, question: str, plan: List[str], **kwargs) -> str:
                """Выполнить план задач (с кэшированием)"""
                history = ""
                final_answer = ""
                
                print("\n--- Выполнение плана ---")
                for i, step in enumerate(plan, 1):
                    print(f"\n-> Выполнение шага {i}/{len(plan)}: {step}")
                    
                    # Попытка загрузки из кэша
                    cached_result = self._load_step_from_cache(i, step)
                    if cached_result:
                        response_text = cached_result
                    else:
                        # Кэш не найден — выполнить шаг
                        prompt = self.prompt_template.format(
                            question=question,
                            plan=plan,
                            history=history if history else "нет",
                            current_step=step
                        )
                        messages = [{"role": "user", "content": prompt}]
                        response_text = self.llm_client.invoke(messages, **kwargs) or ""
                        
                        # Сохранить в кэш
                        self._save_step_to_cache(i, step, response_text)
                    
                    history += f"Шаг {i}: {step}\nРезультат: {response_text}\n\n"
                    final_answer = response_text
                    print(f"▸ Шаг {i} завершён, результат: {final_answer[:100] if len(final_answer) > 100 else final_answer}...")
                
                return final_answer
        
        # Создать PlanAndSolveAgent и заменить Executor
        self.agent = PlanAndSolveAgent(
            name="Эксперт по планированию колонок",
            llm=self.llm,
            custom_prompts=planner_prompts
        )
        
        # Заменить Executor на версию с кэшем
        cached_executor = CachedExecutor(
            llm_client=self.llm,
            prompt_template=planner_prompts["executor"],
            cache_dir=self.cache_dir,
            main_topic=""  # будет установлено в plan_column
        )
        self.agent.executor = cached_executor
    
    def _get_cache_key(self, main_topic: str) -> str:
        """
        Сформировать ключ кэша (хэш темы)
        
        Args:
            main_topic: тема колонки
            
        Returns:
            имя файла кэша
        """
        # Использовать хэш темы как имя файла
        topic_hash = hashlib.md5(main_topic.encode('utf-8')).hexdigest()
        return f"plan_{topic_hash}.json"
    
    def _load_from_cache(self, main_topic: str) -> Optional[ColumnPlan]:
        """
        Загрузить результат планирования из кэша
        
        Args:
            main_topic: тема колонки
            
        Returns:
            экземпляр ColumnPlan или None, если кэша нет
        """
        cache_file = self.cache_dir / self._get_cache_key(main_topic)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Проверить соответствие темы в кэше
            if cache_data.get('topic') != main_topic:
                print(f"▸️  Тема в кэше не совпадает, кэш игнорируется")
                return None
            
            plan_data = cache_data.get('plan')
            if not plan_data:
                return None
            
            plan = ColumnPlan.from_dict(plan_data)
            print(f"▸ Загрузить результат планирования из кэша")
            print(f"   Файл кэша: {cache_file}")
            return plan
        except Exception as e:
            print(f"▸️  Ошибка загрузки кэша: {e}")
            return None
    
    def _save_to_cache(self, main_topic: str, plan: ColumnPlan):
        """
        Сохранить результат планирования в кэш
        
        Args:
            main_topic: тема колонки
            plan: экземпляр ColumnPlan
        """
        cache_file = self.cache_dir / self._get_cache_key(main_topic)
        
        try:
            cache_data = {
                'topic': main_topic,
                'plan': plan.to_dict(),
                'cached_at': get_current_timestamp()  # корректная метка времени кэша
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            print(f"▸ Результат планирования сохранён в кэш: {cache_file}")
        except Exception as e:
            print(f"▸️  Ошибка сохранения кэша: {e}")
    
    def plan_column(self, main_topic: str, use_cache: bool = True) -> ColumnPlan:
        """
        Спланировать план колонки
        
        Args:
            main_topic: тема колонки
            use_cache: использовать кэш (по умолчанию True)
            
        Returns:
            экземпляр ColumnPlan
        """
        # Попытка загрузки из кэша
        if use_cache:
            cached_plan = self._load_from_cache(main_topic)
            if cached_plan:
                print(f"   Заголовок колонки: {cached_plan.column_title}")
                print(f"   Количество тем: {cached_plan.get_topic_count()}")
                return cached_plan
        
        # Кэш не найден — вызвать LLM для планирования
        print(f"\n▸ PlanAndSolve Agent начинает планирование колонки...")
        print(f"   Режим: декомпозиция задачи → пошаговое выполнение")
        print(f"   Тема: {main_topic}")
        
        # Обновить тему Executor (для ключа кэша)
        if hasattr(self.agent.executor, 'main_topic'):
            self.agent.executor.main_topic = main_topic
        
        response = self.agent.run(main_topic)
        
        # Разобрать JSON-ответ
        plan_data = self._extract_json(response)
        plan = ColumnPlan.from_dict(plan_data)
        
        print(f"▸ Планирование завершено")
        print(f"   Заголовок колонки: {plan.column_title}")
        print(f"   Количество тем: {plan.get_topic_count()}")
        
        # Сохранить в кэш
        if use_cache:
            self._save_to_cache(main_topic, plan)
        
        return plan
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Извлечь JSON из ответа (через JSONExtractor)"""
        try:
            return JSONExtractor.extract(
                response,
                required_fields=['column_title', 'topics']
            )
        except Exception as e:
            print(f"▸️  Ошибка извлечения JSON: {e}")
            print(f"   Содержимое ответа (первые 500 символов): {response[:500]}...")
            raise


class ReActAgentWrapper:
    """
    Обёртка ReActAgent для захвата истории и обработки ошибок
    """
    def __init__(self, agent: ReActAgent):
        self.agent = agent
        self.last_history = []  # история последнего запуска
        self.last_response = None  # возвращаемое значение run() (обычно final_answer)
        self.last_raw_responses = []  # все сырые ответы LLM для отладки
    
    def run(self, question: str):
        """
        Запустить агента и захватить историю
        
        Args:
            question: вопрос
        """
        try:
            # Очистить сырые ответы предыдущего запуска
            self.last_raw_responses = []
            
            # Попытка доступа к атрибуту history агента (если есть)
            if hasattr(self.agent, 'current_history'):
                original_history = self.agent.current_history.copy() if self.agent.current_history else []
            elif hasattr(self.agent, 'history'):
                original_history = self.agent.history.copy() if self.agent.history else []
            else:
                original_history = []
            
            # Если у агента есть _parse_output, сохранить оригинал и заменить улучшенной версией
            original_parse = None
            original_invoke = None
            
            if hasattr(self.agent, '_parse_output'):
                original_parse = self.agent._parse_output
                # Использовать единую функцию разбора (обёртка-метод)
                def parse_wrapper(text):
                    return parse_react_output(text)
                self.agent._parse_output = parse_wrapper
            
            # Перехватить вызов LLM для захвата сырого ответа
            if hasattr(self.agent, 'llm') and hasattr(self.agent.llm, 'invoke'):
                original_invoke = self.agent.llm.invoke
                
                def wrapped_invoke(messages, **kwargs):
                    """Обёртка invoke LLM для захвата сырого ответа"""
                    response = original_invoke(messages, **kwargs)
                    if response:
                        self.last_raw_responses.append(response)
                    return response
                
                self.agent.llm.invoke = wrapped_invoke
            
            try:
                response = self.agent.run(question)
                self.last_response = response
                
                # Попытка получить итоговую историю
                if hasattr(self.agent, 'current_history'):
                    self.last_history = self.agent.current_history.copy() if self.agent.current_history else []
                elif hasattr(self.agent, 'history'):
                    self.last_history = self.agent.history.copy() if self.agent.history else []
                else:
                    self.last_history = original_history
                
                return response
            finally:
                # Восстановить оригинальные методы
                if original_parse:
                    self.agent._parse_output = original_parse
                if original_invoke and hasattr(self.agent, 'llm'):
                    self.agent.llm.invoke = original_invoke
                    
        except Exception as e:
            # Даже при ошибке попытаться сохранить историю
            if hasattr(self.agent, 'current_history'):
                self.last_history = self.agent.current_history.copy() if self.agent.current_history else []
            elif hasattr(self.agent, 'history'):
                self.last_history = self.agent.history.copy() if self.agent.history else []
            print(f"▸️  ReActAgentWrapper перехватил исключение: {e}")
            raise


class WriterAgent:
    """
    Агент написания — режим ReActAgent
    
    ReActAgent сочетает рассуждение (Reasoning) и действие (Acting), идеален для сценариев написания с инструментами:
    1. Анализ требований к тексту (рассуждение)
    2. Решение о необходимости поиска (рассуждение)
    3. Вызов поисковых инструментов (действие)
    4. Синтез информации и написание (действие)
    """
    
    def __init__(self, enable_search: bool = True):
        """
        Инициализация агента написания
        
        Args:
            enable_search: включить поиск
        """
        self.llm = LLMService.get_llm()
        self.enable_search = enable_search
        
        # Создать реестр инструментов
        self.tool_registry = ToolRegistry()
        
        # Добавить поисковые инструменты (если включено)
        if enable_search:
            self._setup_search_tool()
        
        # Пользовательский ReAct-промпт
        react_prompt = get_react_writer_prompt() # из prompts.py

        # Создать ReActAgent (разбор заменится в обёртке)
        react_agent = ReActAgent(
            name="Эксперт по созданию контента",
            llm=self.llm,
            tool_registry=self.tool_registry,
            custom_prompt=react_prompt,
            max_steps=10  # до 10 шагов, больше попыток завершить задачу
        )
        
        self.agent = ReActAgentWrapper(react_agent)
    
    def _setup_search_tool(self):
        """Настроить поисковые инструменты (SearchTool и MCPTool)"""
        settings = get_settings()
        
        # Сохранить экземпляр search_tool для wrappers
        self.search_tool = None
        
        # 1. Инициализировать встроенный SearchTool
        try:
            # Проверить наличие API для поиска
            if settings.tavily_api_key or settings.serpapi_api_key:
                self.search_tool = SearchTool(
                    tavily_key=settings.tavily_api_key,
                    serpapi_key=settings.serpapi_api_key
                )
                print("▸ SearchTool (встроенный) инициализирован")
            else:
                print("▸️  API Key для поиска (Tavily/SerpApi) не настроен, пропуск инициализации SearchTool")
        except Exception as e:
            print(f"▸️  Ошибка инициализации SearchTool: {e}")

        # 2. Зарегистрировать wrapper-функции (если search_tool доступен)
        if self.search_tool:
            self._register_search_wrappers()
            
        # 3. Зарегистрировать GitHub MCPTool
        try:
            # Проверить наличие GitHub Token (обычно GITHUB_PERSONAL_ACCESS_TOKEN)
            if os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN"):
                github_tool = MCPTool(
                    name="github",
                    description="Инструмент GitHub: поиск репозиториев, просмотр кода и др.",
                    server_command=["npx", "-y", "@modelcontextprotocol/server-github"],
                    auto_expand=True
                )
                self.tool_registry.register_tool(github_tool)
                print("▸ GitHub MCPTool зарегистрирован")
            else:
                print("▸️  GITHUB_PERSONAL_ACCESS_TOKEN не настроен, пропуск регистрации GitHub MCPTool")
        except Exception as e:
            print(f"▸️  Ошибка регистрации GitHub MCPTool: {e}")

    def _register_search_wrappers(self):
        """Зарегистрировать wrapper-функции поиска под промпт"""
        
        def web_search(query: str) -> str:
            """Общий веб-поиск для свежих новостей и материалов"""
            # SearchTool.run принимает dict
            return str(self.search_tool.run({"query": query}))
        
        def search_recent_info(topic: str) -> str:
            """Поиск свежей информации и новостей"""
            return str(self.search_tool.run({"query": f"{topic} latest info"}))
        
        def search_code_examples(technology: str, task: str) -> str:
            """Поиск примеров кода и туториалов"""
            return str(self.search_tool.run({"query": f"{technology} {task} code examples tutorial"}))
        
        def verify_facts(statement: str) -> str:
            """Проверка фактической точности"""
            return str(self.search_tool.run({"query": f"verify fact: {statement}"}))
        
        self.tool_registry.register_function("web_search", "Общий веб-поиск для свежих новостей и материалов", web_search)
        self.tool_registry.register_function("search_recent_info", "Поиск свежей информации и новостей", search_recent_info)
        self.tool_registry.register_function("search_code_examples", "Поиск примеров кода и туториалов", search_code_examples)
        self.tool_registry.register_function("verify_facts", "Проверка фактической точности", verify_facts)
        print("▸ Wrapper-функции поиска зарегистрированы")
            
    
    def generate_content(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        level: int,
        additional_requirements: str = ""
    ) -> Dict[str, Any]:
        """
        Сгенерировать контент (режим ReAct)
        
        Args:
            node: текущий узел
            context: контекст написания
            level: текущий уровень
            additional_requirements: дополнительные требования
            
        Returns:
            данные сгенерированного контента
        """
        structure_requirements = get_structure_requirements(level)
        word_count = get_word_count(level)
        
        # Сформировать описание задачи написания
        task_description = f"""
Напишите техническую статью для колонки.

Уровень: Level {level}/3
Тема: {node.title}
Описание: {node.description}
Требуемый объём: {word_count} слов (допуск ±10%)

Контекст:
{json.dumps(context, ensure_ascii=False, indent=2)}

Требования к структуре:
{structure_requirements}

Дополнительные требования:
{additional_requirements if additional_requirements else "нет"}

Важно:
- После завершения написания обязательно используйте формат `\n\nFinish[содержимое JSON]`
- Поле `level` в JSON должно быть {level}
- Поле `content` должно содержать полный текст статьи (Markdown)
- Статья должна включать: введение, основную часть (3-5 разделов), практический пример, заключение
"""
        
        try:
            response = self.agent.run(task_description)
            
            # Отладка: вывести сырой ответ LLM (последний)
            print(f"\n{'='*70}")
            print("▸ Сырой ответ LLM ReActAgent:")
            print(f"{'='*70}")
            if self.agent.last_raw_responses:
                # Вывести последний сырой ответ (обычно с Finish[...])
                last_raw = self.agent.last_raw_responses[-1]
                print(last_raw)
                # print(last_raw[:2000] if len(last_raw) > 2000 else last_raw)
                # if len(last_raw) > 2000:
                    # print(f"\n... (ответ слишком длинный, обрезан, всего: {len(last_raw)} символов)")
            else:
                print("▸️  Сырой ответ не захвачен")
            print(f"{'='*70}\n")
            
            # Вывести возвращаемое значение run() (обычно final_answer)
            print(f"▸ Возвращаемое значение ReActAgent.run():")
            print(f"   {response[:500] if response and len(response) > 500 else response}")
            print()
            
            # Проверить валидность ответа
            # Даже при пустом ответе проверить сырой ответ для извлечения
            if not response or (isinstance(response, str) and not response.strip()):
                print("▸️  ReActAgent вернул пустой ответ")
                print(f"   Собрано записей истории: {len(self.agent.last_history)}")
                
                # Попытка извлечь контент из последнего сырого ответа
                if self.agent.last_raw_responses:
                    last_raw = self.agent.last_raw_responses[-1]
                    print(f"   Попытка извлечь контент из последнего сырого ответа (длина: {len(last_raw)} символов)...")
                    # Попытка прямого извлечения JSON
                    try:
                        content_data = self._extract_json(last_raw)
                        # Проверить обязательные поля в извлечённом JSON
                        if not isinstance(content_data, dict):
                            raise ValueError("Извлечённое содержимое не является словарём")
                        if 'content' not in content_data:
                            print(f"   ▸️  В извлечённом JSON отсутствует поле 'content'")
                            print(f"   Доступные поля: {list(content_data.keys())}")
                            raise ValueError("В извлечённом JSON отсутствует поле 'content'")
                        print("▸ Контент успешно извлечён из сырого ответа")
                        return content_data
                    except Exception as e:
                        print(f"   ▸️  Ошибка извлечения из сырого ответа: {e}")
                
                # При неудаче — fallback
                return self._generate_content_with_history(
                    node, context, level, structure_requirements, word_count,
                    self.agent.last_history, task_description
                )
            
            # Проверить, является ли ответ сообщением об ошибке
            if "не удалось завершить за отведённое число шагов" in response or "извините" in response or "процесс завершён" in response:
                print("▸️  ReActAgent достиг лимита шагов или не смог завершить задачу")
                print(f"   Собрано записей истории: {len(self.agent.last_history)}")
                
                # Даже при сообщении об ошибке попытаться извлечь контент из последнего сырого ответа
                if self.agent.last_raw_responses:
                    last_raw = self.agent.last_raw_responses[-1]
                    print(f"   Попытка извлечь контент из последнего сырого ответа (длина: {len(last_raw)} символов)...")
                    try:
                        content_data = self._extract_json(last_raw)
                        # Проверить обязательные поля в извлечённом JSON
                        if not isinstance(content_data, dict):
                            raise ValueError("Извлечённое содержимое не является словарём")
                        if 'content' not in content_data:
                            print(f"   ▸️  В извлечённом JSON отсутствует поле 'content'")
                            print(f"   Доступные поля: {list(content_data.keys())}")
                            raise ValueError("В извлечённом JSON отсутствует поле 'content'")
                        print("▸ Контент извлечён из сырого ответа (несмотря на сообщение об ошибке ReActAgent)")
                        return content_data
                    except Exception as e:
                        print(f"   ▸️  Ошибка извлечения из сырого ответа: {e}")
                
                # При неудаче — генерация на основе истории
                return self._generate_content_with_history(
                    node, context, level, structure_requirements, word_count,
                    self.agent.last_history, task_description
                )
            
            # Если response — плейсхолдер вроде "содержимое JSON", извлечь из сырого ответа
            if response.strip() in ["содержимое JSON", "JSON", "содержимое"]:
                print(f"▸️  ReActAgent вернул плейсхолдер '{response}', попытка извлечения из сырого ответа...")
                if self.agent.last_raw_responses:
                    last_raw = self.agent.last_raw_responses[-1]
                    print(f"   Извлечение из последнего сырого ответа (длина: {len(last_raw)} символов)...")
                    try:
                        content_data = self._extract_json(last_raw)
                        if isinstance(content_data, dict) and 'content' in content_data:
                            print("▸ Контент успешно извлечён из сырого ответа")
                            return content_data
                    except Exception as e:
                        print(f"   ▸️  Ошибка извлечения из сырого ответа: {e}")
            
            content_data = self._extract_json(response)
            
            # Проверить обязательные поля в извлечённом JSON
            if not isinstance(content_data, dict):
                raise ValueError(f"Извлечённое содержимое не словарь: {type(content_data)}")
            if 'content' not in content_data:
                print(f"▸️  В извлечённом JSON отсутствует поле 'content'")
                print(f"   Доступные поля: {list(content_data.keys())}")
                print(f"   Содержимое ответа (первые 500 символов): {response[:500]}")
                
                # Если из response извлечь не удалось, попробовать сырой ответ
                if self.agent.last_raw_responses:
                    last_raw = self.agent.last_raw_responses[-1]
                    print(f"   Попытка извлечения из последнего сырого ответа (длина: {len(last_raw)} символов)...")
                    try:
                        content_data = self._extract_json(last_raw)
                        if isinstance(content_data, dict) and 'content' in content_data:
                            print("▸ Контент успешно извлечён из сырого ответа")
                            return content_data
                    except Exception as e:
                        print(f"   ▸️  Ошибка извлечения из сырого ответа: {e}")
                
                raise ValueError("В извлечённом JSON отсутствует поле 'content'")
            
            return content_data
        except Exception as e:
            print(f"▸️  Ошибка выполнения ReActAgent: {e}")
            import traceback
            traceback.print_exc()
            print(f"   Собрано записей истории: {len(self.agent.last_history)}")
            print("   Попытка генерации контента на основе истории...")
            return self._generate_content_with_history(
                node, context, level, structure_requirements, word_count,
                self.agent.last_history, task_description
            )
    
    def _generate_content_with_history(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        level: int,
        structure_requirements: str,
        word_count: int,
        history: List[str],
        original_task: str
    ) -> Dict[str, Any]:
        """
        При сбое ReActAgent — генерация через SimpleAgent на основе истории
        
        Args:
            history: история ReActAgent (Thought, Action, Observation)
        """
        from hello_agents import SimpleAgent
        
        fallback_agent = SimpleAgent(
            name="Эксперт по созданию контента (резервный)",
            llm=self.llm,
            system_prompt="Вы — профессиональный автор контента, специализирующийся на технических колонках."
        )
        
        # Сформировать описание задачи с историей
        history_summary = ""
        if history:
            history_summary = "\n\n## Частичная история написания:\n"
            for i, item in enumerate(history[-10:], 1):  # только последние 10 записей
                history_summary += f"{i}. {item}\n"
            history_summary += "\nПродолжите задачу написания на основе информации выше.\n"
        
        task = f"""
Напишите техническую статью для колонки.

Тема: {node.title}
Описание: {node.description}
Требуемый объём: {word_count} слов

Требования к структуре:
{structure_requirements}
{history_summary}

Выведите контент напрямую в формате JSON:
{{
  "title": "{node.title}",
  "level": {level},
  "content": "Полный текст статьи (markdown, с введением, основной частью, примером и заключением)",
  "word_count": фактический объём,
  "needs_expansion": false,
  "subsections": [],
  "metadata": {{}}
}}
"""
        
        print(f"▸ Генерация контента через SimpleAgent на основе истории...")
        response = fallback_agent.run(task)
        return self._extract_json(response)
    
    def revise_content(
        self,
        original_content: str,
        review_result: ReviewResult,
        level: int
    ) -> Dict[str, Any]:
        """
        Отредактировать контент по результатам оценки
        
        Args:
            original_content: исходный контент
            review_result: результат оценки
            level: уровень
            
        Returns:
            данные отредактированного контента
        """
        # Сформировать задачу правки
        task_description = f"""
## Задача правки

**Исходный контент**:
{original_content[:500]}...

**Оценка**: {review_result.score}/100
**Уровень оценки**: {review_result.grade}

**Основные проблемы**:
{json.dumps(review_result.detailed_feedback.get('issues', [])[:3], ensure_ascii=False, indent=2)}

**Рекомендации по правкам**:
{json.dumps(review_result.revision_plan.get('priority_changes', []), ensure_ascii=False, indent=2)}

Выполните правки в режиме ReAct:
1. Проанализируйте ключевые требования оценки
2. Решите, нужен ли поиск новой информации
3. Отредактируйте контент
4. Выведите результат через Finish[изменённое содержимое JSON]
"""
        
        response = self.agent.run(task_description)
        revised_data = self._extract_json(response)
        
        return revised_data
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Извлечь JSON из ответа (через JSONExtractor)"""
        try:
            return JSONExtractor.extract(
                response,
                required_fields=['content'],
                fallback_fields={
                    'subsections': [],
                    'metadata': {},
                    'needs_expansion': False
                }
            )
        except Exception as e:
            print(f"▸️  Ошибка при извлечении JSON: {e}")
            print(f"   Содержимое ответа (первые 1000 символов): {response[:1000]}")
            raise


class ReviewerAgent:
    """
    Агент оценки — режим SimpleAgent
    
    Оценивает качество сгенерированного контента, выдаёт подробную оценку и рекомендации
    """
    
    def __init__(self):
        from hello_agents import SimpleAgent
        from prompts import get_reviewer_prompt
        
        self.llm = LLMService.get_llm()
        self.reviewer_prompt = get_reviewer_prompt()
        
        self.agent = SimpleAgent(
            name="Эксперт по оценке контента",
            llm=self.llm,
            system_prompt="Вы — строгий профессиональный эксперт по оценке контента, умеющий оценивать качество статей и давать конструктивные рекомендации."
        )
    
    def review_content(
        self,
        content: str,
        level: int,
        target_word_count: int,
        key_points: List[str]
    ) -> 'ReviewResult':
        """
        Оценить контент
        
        Args:
            content: контент для оценки
            level: уровень контента
            target_word_count: целевой объём
            key_points: ключевые пункты
            
        Returns:
            экземпляр ReviewResult
        """
        print(f"\n▸ ReviewerAgent начинает оценку контента...")
        print(f"   Длина контента: {len(content)} символов")
        print(f"   Целевой объём: {target_word_count}")
        
        # Сформировать задачу оценки
        task = self.reviewer_prompt.format(
            level=level,
            target_word_count=target_word_count,
            key_points=json.dumps(key_points, ensure_ascii=False),
            content=content
        )
        
        response = self.agent.run(task)
        review_data = self._extract_json(response)
        
        # Создать экземпляр ReviewResult
        result = ReviewResult.from_dict(review_data)
        
        print(f"▸ Оценка завершена")
        print(f"   Оценка: {result.score}/100 ({result.grade})")
        print(f"   Требуются правки: {'да' if result.needs_revision else 'нет'}")
        
        return result
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Извлечь JSON из ответа"""
        try:
            return JSONExtractor.extract(
                response,
                required_fields=['score', 'grade'],
                fallback_fields={
                    'dimension_scores': {},
                    'detailed_feedback': {'strengths': [], 'issues': []},
                    'revision_plan': {'priority_changes': [], 'minor_improvements': []},
                    'needs_revision': True,
                    'estimated_revision_effort': '',
                    'reviewer_notes': ''
                }
            )
        except Exception as e:
            print(f"▸️  Ошибка разбора результата оценки: {e}")
            # Вернуть оценку по умолчанию (требуются правки)
            return {
                'score': 60,
                'grade': 'Требует доработки',
                'dimension_scores': {},
                'detailed_feedback': {'strengths': [], 'issues': [{'problem': 'Ошибка разбора результата оценки'}]},
                'revision_plan': {'priority_changes': [], 'minor_improvements': []},
                'needs_revision': True,
                'estimated_revision_effort': 'неизвестно',
                'reviewer_notes': f'Ошибка разбора результата оценки: {str(e)}'
            }


class RevisionAgent:
    """
    Агент правок — режим SimpleAgent
    
    Отредактировать контент по результатам оценки
    """
    
    def __init__(self):
        from hello_agents import SimpleAgent
        from prompts import get_revision_prompt
        
        self.llm = LLMService.get_llm()
        self.revision_prompt = get_revision_prompt()
        
        self.agent = SimpleAgent(
            name="Эксперт по правкам контента",
            llm=self.llm,
            system_prompt="Вы — профессиональный автор, умеющий редактировать и улучшать статьи по замечаниям оценки."
        )
    
    def revise_content(
        self,
        original_content: str,
        review_result: 'ReviewResult',
        target_word_count: int
    ) -> Dict[str, Any]:
        """
        Отредактировать контент по результатам оценки
        
        Args:
            original_content: исходный контент
            review_result: результат оценки
            target_word_count: целевой объём
            
        Returns:
            данные отредактированного контента
        """
        print(f"\n▸ RevisionAgent начинает правку контента...")
        print(f"   Исходная оценка: {review_result.score}/100")
        
        current_word_count = len(original_content)
        word_count_min = int(target_word_count * 0.9)
        word_count_max = int(target_word_count * 1.1)
        
        # Рассчитать рекомендацию по объёму
        if current_word_count < word_count_min:
            word_count_adjustment = f"нужно добавить около {word_count_min - current_word_count} слов"
        elif current_word_count > word_count_max:
            word_count_adjustment = f"нужно сократить около {current_word_count - word_count_max} слов"
        else:
            word_count_adjustment = "объём в допустимом диапазоне"
        
        # Форматировать информацию оценки
        strengths = "\n".join([f"- {s}" for s in review_result.detailed_feedback.get('strengths', [])])
        issues = "\n".join([
            f"- [{issue.get('category', 'неизвестно')}] {issue.get('problem', '')}: {issue.get('suggestion', '')}"
            for issue in review_result.detailed_feedback.get('issues', [])
        ])
        priority_changes = "\n".join([
            f"- **{change.get('section', '')}**: {change.get('action', '')} - {change.get('detail', '')}"
            for change in review_result.revision_plan.get('priority_changes', [])
        ])
        minor_improvements = "\n".join([
            f"- {imp.get('section', '')}: {imp.get('detail', '')}"
            for imp in review_result.revision_plan.get('minor_improvements', [])
        ])
        
        # Сформировать задачу правки
        task = self.revision_prompt.format(
            original_content=original_content,
            score=review_result.score,
            grade=review_result.grade,
            strengths=strengths or "нет",
            issues=issues or "нет",
            reviewer_notes=review_result.reviewer_notes or "нет",
            priority_changes=priority_changes or "нет",
            minor_improvements=minor_improvements or "нет",
            word_count_range=f"{word_count_min}-{word_count_max}",
            current_word_count=current_word_count,
            word_count_adjustment=word_count_adjustment
        )
        
        response = self.agent.run(task)
        revised_data = self._extract_json(response)
        
        print(f"▸ Правка завершена")
        print(f"   Объём после правки: {revised_data.get('word_count', len(revised_data.get('revised_content', '')))}")
        
        return revised_data
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Извлечь JSON из ответа"""
        try:
            data = JSONExtractor.extract(
                response,
                required_fields=['revised_content'],
                fallback_fields={
                    'revision_summary': {'major_changes': [], 'minor_changes': [], 'preserved_strengths': []},
                    'word_count': 0,
                    'word_count_change': ''
                }
            )
            # Если word_count отсутствует — вычислить
            if not data.get('word_count'):
                data['word_count'] = len(data.get('revised_content', ''))
            return data
        except Exception as e:
            print(f"▸️  Ошибка разбора результата правки: {e}")
            raise


class ReflectionWriterAgent:
    """
    Агент рефлексивного написания — режим ReflectionAgent
    
    ReflectionAgent улучшает результат через саморефлексию и итерации, объединяя оценку и правки:
    1. Сгенерировать черновик
    2. Самооценка (рефлексия)
    3. Правка по рефлексии (оптимизация)
    4. Достичь стандарта качества
    """
    
    def __init__(self):
        self.llm = LLMService.get_llm()
        
        # Пользовательские промпты Reflection
        reflection_prompts = {
            "initial": """
Вы — профессиональный автор. Напишите черновик следующего контента:

{task}

Выведите полный контент в формате JSON.
""",
            "reflect": """
Вы — строгий эксперт по оценке контента. Оцените следующий контент:

# Задача написания: {task}
# Черновик: {content}

Оцените по следующим критериям:
1. **Качество содержания** (40 баллов): точность, полнота, глубина, оригинальность
2. **Структура и логика** (30 баллов): чёткая иерархия, связность, плавные переходы
3. **Язык** (20 баллов): читаемость, профессионализм, точность
4. **Форматирование** (10 баллов): объём, корректность формата, аккуратная вёрстка

Если качество высокое (85+ баллов), ответьте «правки не требуются».
Иначе подробно укажите проблемы и дайте конкретные рекомендации.
""",
            "refine": """
Оптимизируйте контент по замечаниям оценки:

# Исходная задача: {task}
# Текущий контент: {last_attempt}
# Замечания оценки: {feedback}

Выведите полный оптимизированный контент в формате JSON.
"""
        }
        
        self.agent = ReflectionAgent(
            name="Эксперт рефлексивного написания",
            llm=self.llm,
            custom_prompts=reflection_prompts,
            max_iterations=2  # максимум 2 цикла рефлексии
        )
    
    def generate_and_refine_content(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        level: int
    ) -> Dict[str, Any]:
        """
        Сгенерировать и оптимизировать контент через рефлексию
        
        Args:
            node: текущий узел
            context: контекст написания
            level: текущий уровень
            
        Returns:
            данные оптимизированного контента
        """
        print(f"\n▸ ReflectionAgent начинает написание и саморефлексию...")
        print(f"   Режим: черновик → самооценка → оптимизация")
        
        structure_requirements = get_structure_requirements(level)
        word_count = get_word_count(level)
        
        task_description = f"""
## Задача написания

**Уровень**: Level {level}/3
**Тема**: {node.title}
**Описание**: {node.description}
**Требуемый объём**: {word_count} слов (допуск ±10%)

**Требования к структуре**:
{structure_requirements}

**Контекст**:
{json.dumps(context, ensure_ascii=False, indent=2)}

Выведите полный контент в формате JSON:
```json
{{
  "title": "Заголовок раздела",
  "level": {level},
  "content": "Текст статьи (формат markdown)",
  "word_count": фактический объём,
  "needs_expansion": true/false,
  "subsections": [...],
  "metadata": {{...}}
}}
```
"""
        
        response = self.agent.run(task_description)
        content_data = self._extract_json(response)
        
        print(f"▸ ReflectionAgent завершил рефлексию и оптимизацию")
        
        return content_data
    
    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Извлечь JSON из ответа (через JSONExtractor)"""
        try:
            return JSONExtractor.extract(
                response,
                required_fields=['content'],
                fallback_fields={
                    'subsections': [],
                    'metadata': {},
                    'needs_expansion': False
                }
            )
        except Exception as e:
            print(f"▸️  Ошибка разбора JSON: {e}")
            raise

