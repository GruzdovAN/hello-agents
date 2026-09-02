"""Code Plan Agent — интеллектуальный инструмент планирования кода с функцией отражения Reflection."""

import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from hello_agents.core.agent import Agent
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.message import Message
from hello_agents.core.streaming import StreamEvent, StreamEventType
from hello_agents.core.lifecycle import LifecycleHook
from hello_agents.tools.registry import ToolRegistry


class PlanMemory:
    """Модуль памяти плана, используемый для хранения трека генерации и записи отражения плана кода."""
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str, metadata: Optional[Dict] = None):
        """Добавить новую запись в память"""
        self.records.append({
            "type": record_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })

    def get_trajectory(self) -> str:
        """Отформатируйте все записи памяти в связный строковый текст."""
        trajectory = ""
        for record in self.records:
            if record['type'] == 'plan':
                trajectory += f"--- План кода ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- Рефлексивная обратная связь ---\n{record['content']}\n\n"
            elif record['type'] == 'revision':
                trajectory += f"---Оптимизированный план ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_plan(self) -> str:
        """Получите последний план кода"""
        for record in reversed(self.records):
            if record['type'] in ['plan', 'revision']:
                return record['content']
        return ""

    def get_last_reflection(self) -> str:
        """Получите отзыв о своем последнем размышлении"""
        for record in reversed(self.records):
            if record['type'] == 'reflection':
                return record['content']
        return ""


class CodePlanAgent(Agent):
    """Code Plan Agent — интеллектуальный инструмент планирования кода с функцией отражения Reflection.

    Основные компетенции:
    1. Генерация плана кода. Создайте план реализации структурированного кода на основе описания требований.
    2. Самоанализ: провести оценку качества и внести предложения по улучшению созданного плана кода.
    3. Итеративная оптимизация: оптимизируйте план кода на основе результатов отражения.
    4. Вызов инструмента поддержки (опционально)

    Выходной формат:
    - Планы кода имеют структурированный формат и содержат несколько этапов.
    - Каждый шаг включает: номер шага, описание задачи, точки реализации, ожидаемый результат.

    Светоотражающий размер:
    - Полнота: охватывает ли план все требования?
    - Технико-экономическое обоснование: осуществимо ли техническое решение.
    - Эффективность: есть ли возможности для оптимизации производительности?
    - Ремонтопригодность: понятна ли структура кода?
    - Безопасность: существуют ли риски безопасности?"""

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_reflection_iterations: int = 2,
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True,
        max_tool_iterations: int = 3
    ):
        """Инициализация агента CodePlanAgent

        Аргументы:
            имя: Имя агента
            llm: экземпляр LLM
            system_prompt: слово системной подсказки (определяет роли и поведение)
            конфигурация: объект конфигурации
            max_reflection_iterations: Максимальное количество итераций отражения.
            tool_registry: реестр инструментов (необязательно)
            Enable_tool_calling: Включить ли вызов инструмента
            max_tool_iterations: Максимальное количество итераций вызова инструмента."""
        # Default system_prompt — эксперт по планированию кода

        default_system_prompt = """Вы старший архитектор программного обеспечения и эксперт по планированию кода.
Вы хорошо умеете переводить бизнес-требования в четкие и действенные планы реализации кода.

## Основные обязанности
1. Анализ требований и создание плана реализации структурированного кода.
2. Убедитесь, что план охватывает все основные функции и крайние случаи.
3. Разработайте разумное разделение модулей и определение интерфейса.
4. Учитывайте удобство сопровождения кода, масштабируемость и производительность.

## Требования к формату вывода
Пожалуйста, выведите план кода в следующем структурированном формате:

```code_plan
## Обзор проекта
[Краткое описание целей и основных особенностей проекта]

## Стек технологий
- Язык: [Язык программирования]
- Рамка: [Основной кадр]
- База данных: [Тип базы данных]
- Прочее: [Основные зависимости]

## Структура каталогов
```
[Структура каталогов проекта]
```

## Этапы реализации
1. [Описание шага 1]
   - Точки реализации: [Основные детали реализации]
   - Путь к файлу: [участвующий файл]
   - ожидаемый результат: [ожидаемый результат]

2. [Описание шага 2]
   - Точки реализации: [Основные детали реализации]
   - Путь к файлу: [участвующий файл]
   - ожидаемый результат: [ожидаемый результат]

...

## Дизайн клавиш
- [Проектное решение 1]: [Объясните почему]
- [Проектное решение 2]: [Объясните почему]

## Примечания
- [Примечание 1]
- [Примечание 2]
```

Пожалуйста, убедитесь, что план подробный, ясный и выполнимый."""

        super().__init__(
            name,
            llm,
            system_prompt or default_system_prompt,
            config,
            tool_registry=tool_registry
        )

        self.max_reflection_iterations = max_reflection_iterations
        self.memory = PlanMemory()
        self.enable_tool_calling = enable_tool_calling
        self.max_tool_iterations = max_tool_iterations

    def run(self, input_text: str, **kwargs) -> str:
        """Запустите агент CodePlanAgent.

        Аргументы:
            input_text: описание требования
            **kwargs: другие параметры (температура, max_tokens и т. д.)

        Возврат:
            Окончательный оптимизированный план кода"""
        print(f"\n🤖 {self.name} начинает обработку задач планирования кода: {input_text[:50]}...")

        # сбросить память

        self.memory = PlanMemory()

        # 1. Создайте первоначальный план кода.

        print("\n--- Этап 1. Создание первоначального плана кода ---")
        initial_plan = self._generate_code_plan(input_text, **kwargs)
        self.memory.add_record("plan", initial_plan, {"phase": "initial"})

        print(f"\n✅ Первоначальный план создан:\n{initial_plan}")

        # 2. Итеративное отражение и оптимизация

        for i in range(self.max_reflection_iterations):
            print(f"\n--- Фаза 2: {i+1}/{self.max_reflection_iterations} раунд оптимизации отражения ---")

            # а. Подумайте о текущих планах

            print("\n->Размышляя о плане...")
            last_plan = self.memory.get_last_plan()
            reflection = self._reflect_on_plan(input_text, last_plan, **kwargs)
            self.memory.add_record("reflection", reflection, {"iteration": i + 1})

            print(f"\n💡Результаты отражения:\n{reflection}")

            # б. Проверьте, нужно ли останавливаться

            if "Никаких улучшений не требуется" in reflection or "no need for improvement" in reflection.lower():
                print("\n ✅Поразмыслив, я считаю, что план больше не нуждается в улучшении и задача выполнена.")
                break

            # в. Оптимизировать план

            print("\n->Оптимизация плана кода...")
            refined_plan = self._refine_plan(input_text, last_plan, reflection, **kwargs)
            self.memory.add_record("revision", refined_plan, {"iteration": i + 1})

            print(f"\n🔄 Оптимизированный план:\n{refined_plan}")

        final_plan = self.memory.get_last_plan()
        print(f"\n--- 🎉 Миссия выполнена ---\nОкончательный план кода:\n{final_plan}")

        # Сохранить в историю

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_plan, "assistant"))

        return final_plan

    def _generate_code_plan(self, requirements: str, **kwargs) -> str:
        """Создать первоначальный план кода

        Аргументы:
            требования: описание требования
            **kwargs: параметры вызова LLM.

        Возврат:
            текст плана кода"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"""Создайте подробный план реализации кода на основе следующего описания требований:

## Описание требования
{требования}

Пожалуйста, выведите план кода в указанном формате."""}
        ]

        return self._get_llm_response(messages, **kwargs)

    def _reflect_on_plan(self, requirements: str, plan: str, **kwargs) -> str:
        """Рефлексивная оценка планов кода

        Аргументы:
            требования: первоначальные требования
            план: текущий план кода
            **kwargs: параметры вызова LLM.

        Возврат:
            Светоотражающий текст обратной связи"""
        reflection_prompt = f"""Вы старший эксперт по технической экспертизе. Пожалуйста, проведите тщательную оценку следующих планов кода:

## Исходные требования
{требования}

## Текущий план кода
{план}

## Просмотр размеров
Пожалуйста, оцените по следующим параметрам:

1. **Полнота**. Охватывает ли план все основные требования? Есть ли недостающие функции?
2. **Осуществимость**: Возможно ли техническое решение? Есть ли технические риски?
3. **Рациональность архитектуры**: разумно ли разделение модулей? Дизайн интерфейса понятен?
4. **Удобство обслуживания**: понятна ли структура кода? Соблюдаются ли лучшие практики?
5. **Аспекты производительности**. Рассматривалась ли оптимизация производительности? Существуют ли потенциальные узкие места производительности?
6. **Безопасность**: существуют ли риски безопасности? Вам нужно добавить меры безопасности?
7. **Тестовое покрытие**: учитывается ли стратегия тестирования? Охватываются ли тестами критические пути?

## Требования к выводу
Пожалуйста, дайте конкретные предложения по улучшению. Если план уже хорош, ответьте: «Улучшений не требуется»."""

        messages = [
            {"role": "system", "content": "Вы строгий технический обозреватель, умеющий выявлять потенциальные проблемы в планах кода и предлагать улучшения."},
            {"role": "user", "content": reflection_prompt}
        ]

        return self._get_llm_response(messages, **kwargs)

    def _refine_plan(self, requirements: str, current_plan: str, feedback: str, **kwargs) -> str:
        """Оптимизация плана кода на основе отзывов

        Аргументы:
            требования: первоначальные требования
            current_plan: текущий план кода
            обратная связь: рефлексивная обратная связь
            **kwargs: параметры вызова LLM.

        Возврат:
            Оптимизированный план кода"""
        refinement_prompt = f"""Пожалуйста, оптимизируйте следующий план кода на основе отзывов отзывов:

## Исходные требования
{требования}

## Текущий план кода
{текущий_план}

## Просмотрите отзыв
{отзыв}

## Требования к оптимизации
Пожалуйста, измените и улучшите план кода на основе отзывов, чтобы гарантировать:
1. Устраните любые проблемы, отмеченные в отзыве.
2. Держите план в структурированном формате
3. Предоставьте конкретные планы улучшений.

Пожалуйста, выведите полный оптимизированный план кода."""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": refinement_prompt}
        ]

        return self._get_llm_response(messages, **kwargs)

    def _get_llm_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Позвоните в LLM и получите полный ответ (поддерживается вызов функций)

        Аргументы:
            сообщения: список сообщений
            **kwargs: другие параметры

        Возврат:
            Текст ответа LLM"""
        # Если вызов инструмента не включен, вернитесь напрямую

        if not self.enable_tool_calling or not self.tool_registry:
            llm_response = self.llm.invoke(messages, **kwargs)
            return llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

        # Включить режим вызова инструмента

        tool_schemas = self._build_tool_schemas()
        current_iteration = 0

        while current_iteration < self.max_tool_iterations:
            current_iteration += 1

            try:
                response = self.llm.invoke_with_tools(
                    messages=messages,
                    tools=tool_schemas,
                    tool_choice="auto",
                    **kwargs
                )
            except Exception as e:
                print(f"❌ Не удалось позвонить в LLM: {e}")
                break

            response_message = response.choices[0].message

            # Обработка вызовов инструментов

            tool_calls = response_message.tool_calls
            if not tool_calls:
                # Инструмент не вызывается, возвращается текстовый ответ

                return response_message.content or ""

            # Добавить сообщение помощника в историю

            messages.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            })

            # Выполнить все вызовы инструментов

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id

                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as e:
                    print(f"❌ Не удалось проанализировать параметры инструмента: {e}.")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": f"Ошибка: неправильный формат аргумента — {str(e)}"
                    })
                    continue

                # Инструменты выполнения (повторное использование методов базового класса)

                result = self._execute_tool_call(tool_name, arguments)

                # Добавить результаты инструмента в сообщение

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result
                })

        # Если максимальное количество итераций превышено, получить последний ответ

        if current_iteration >= self.max_tool_iterations:
            llm_response = self.llm.invoke(messages, **kwargs)
            return llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

        return ""

    async def arun_stream(
        self,
        input_text: str,
        on_start: LifecycleHook = None,
        on_finish: LifecycleHook = None,
        on_error: LifecycleHook = None,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """Потоковое выполнение CodePlanAgent

        Возврат в реальном времени:
        - Результаты этапа разработки плана
        - Мыслительный процесс на стадии размышления
        - Выход этапа оптимизации

        Аргументы:
            input_text: ввод пользователя
            on_start: начать хук
            on_finish: крючок завершения
            on_error: ловушка ошибки
            **kwargs: другие параметры

        Выход:
            StreamEvent: событие потоковой передачи"""
        # Отправить стартовое событие

        yield StreamEvent.create(
            StreamEventType.AGENT_START,
            self.name,
            input_text=input_text
        )

        try:
            # Этап 1. Создание плана кода

            yield StreamEvent.create(
                StreamEventType.STEP_START,
                self.name,
                phase="plan_generation",
                description="Создать первоначальный план кода"
            )

            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})

            plan_prompt = f"""Создайте подробный план реализации кода на основе следующего описания требований:

## Описание требования
{input_text}

Пожалуйста, выведите план кода в указанном формате."""

            messages.append({"role": "user", "content": plan_prompt})

            initial_plan = ""
            async for chunk in self.llm.astream_invoke(messages, **kwargs):
                initial_plan += chunk
                yield StreamEvent.create(
                    StreamEventType.LLM_CHUNK,
                    self.name,
                    chunk=chunk,
                    phase="plan_generation"
                )

            yield StreamEvent.create(
                StreamEventType.STEP_FINISH,
                self.name,
                phase="plan_generation",
                result=initial_plan
            )

            # Этап 2: Цикл размышлений и оптимизации

            current_plan = initial_plan

            for iteration in range(self.max_reflection_iterations):
                # этап отражения

                yield StreamEvent.create(
                    StreamEventType.STEP_START,
                    self.name,
                    phase="reflection",
                    iteration=iteration + 1,
                    description=f"{итерация + 1} отражение"
                )

                reflection_prompt = f"""Вы старший эксперт по технической экспертизе. Пожалуйста, проведите тщательную оценку следующих планов кода:

## Исходные требования
{input_text}

## Текущий план кода
{текущий_план}

## Просмотр размеров
Пожалуйста, оцените по следующим параметрам:
1. Полнота: охватывает ли план все основные требования?
2. Осуществимость: осуществимо ли техническое решение?
3. Рациональность архитектуры: разумно ли разделение модулей?
4. Удобство сопровождения: понятна ли структура кода?
5. Вопросы производительности. Рассматривалась ли оптимизация производительности?
6. Безопасность: существуют ли риски безопасности?
7. Тестовое покрытие: рассмотрена ли стратегия тестирования?

Пожалуйста, дайте конкретные предложения по улучшению. Если план уже хорош, ответьте: «Улучшений не требуется»."""

                reflection_messages = [{"role": "user", "content": reflection_prompt}]

                reflection = ""
                async for chunk in self.llm.astream_invoke(reflection_messages, **kwargs):
                    reflection += chunk
                    yield StreamEvent.create(
                        StreamEventType.THINKING,
                        self.name,
                        chunk=chunk,
                        phase="reflection",
                        iteration=iteration + 1
                    )

                yield StreamEvent.create(
                    StreamEventType.STEP_FINISH,
                    self.name,
                    phase="reflection",
                    iteration=iteration + 1,
                    reflection=reflection
                )

                # Проверьте, нужно ли его остановить

                if "Никаких улучшений не требуется" in reflection or "no need for improvement" in reflection.lower():
                    break

                # Этап оптимизации

                yield StreamEvent.create(
                    StreamEventType.STEP_START,
                    self.name,
                    phase="refinement",
                    iteration=iteration + 1,
                    description=f"{итерация + 1}-я оптимизация"
                )

                refinement_prompt = f"""Пожалуйста, оптимизируйте следующий план кода на основе отзывов отзывов:

## Исходные требования
{input_text}

## Текущий план кода
{текущий_план}

## Просмотрите отзыв
{отражение}

Пожалуйста, выведите полный оптимизированный план кода."""

                refinement_messages = [{"role": "user", "content": refinement_prompt}]

                refined_plan = ""
                async for chunk in self.llm.astream_invoke(refinement_messages, **kwargs):
                    refined_plan += chunk
                    yield StreamEvent.create(
                        StreamEventType.LLM_CHUNK,
                        self.name,
                        chunk=chunk,
                        phase="refinement",
                        iteration=iteration + 1
                    )

                yield StreamEvent.create(
                    StreamEventType.STEP_FINISH,
                    self.name,
                    phase="refinement",
                    iteration=iteration + 1,
                    result=refined_plan
                )

                current_plan = refined_plan

            # Отправить событие завершения

            yield StreamEvent.create(
                StreamEventType.AGENT_FINISH,
                self.name,
                result=current_plan,
                total_iterations=self.max_reflection_iterations
            )

            # сохранить в историю

            self.add_message(Message(input_text, "user"))
            self.add_message(Message(current_plan, "assistant"))

        except Exception as e:
            # Отправить событие ошибки

            yield StreamEvent.create(
                StreamEventType.ERROR,
                self.name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def get_plan_trajectory(self) -> str:
        """Получите полную информацию о создании плана"""
        return self.memory.get_trajectory()


def create_code_plan_agent(llm: HelloAgentsLLM) -> CodePlanAgent:
    """Удобная фабричная функция для создания экземпляров CodePlanAgent.

    Аргументы:
        llm: экземпляр LLM

    Возврат:
        Экземпляр CodePlanAgent"""
    return CodePlanAgent(
        name="CodePlanAgent",
        llm=llm,
        max_reflection_iterations=2
    )
