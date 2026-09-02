"""Расширенная версия SimpleAgent — поддерживает вызовы инструментов потоковой передачи."""

import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, AsyncGenerator, TYPE_CHECKING, Union

from hello_agents.agents.simple_agent import SimpleAgent
from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.config import Config
from hello_agents.core.message import Message
from hello_agents.core.streaming import StreamEvent, StreamEventType

# Импорт LLM HelloClaw (потоковые инструменты)

from .enhanced_llm import EnhancedHelloAgentsLLM, StreamToolEventType

if TYPE_CHECKING:
    from hello_agents.tools.registry import ToolRegistry


class EnhancedSimpleAgent(SimpleAgent):
    """Расширенная версия SimpleAgent, поддерживает вызов инструмента потоковой передачи.

    Наследуйте SimpleAgent от hello_agents и добавьте:
    - Истинный вызов инструмента потоковой передачи (с использованием EnhancedHelloAgentsLLM)
    - Отправка статуса вызова инструмента в режиме реального времени

    Примечание:
        Рекомендуется использовать EnhancedHelloAgentsLLM для полной поддержки вызовов инструментов потоковой передачи.
        При использовании простого HelloAgentsLLM вызовы инструментов потоковой передачи вернутся в непотоковый режим базового класса."""

    def __init__(
        self,
        name: str,
        llm: Union[HelloAgentsLLM, EnhancedHelloAgentsLLM],
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True,
        max_tool_iterations: int = 10,
    ):
        """Инициализация EnhancedSimpleAgent

        Аргументы:
            имя: Имя агента
            llm: экземпляр LLM (рекомендуется EnhancedHelloAgentsLLM)
            system_prompt: слово системной подсказки
            конфигурация: объект конфигурации
            tool_registry: реестр инструментов (необязательно)
            Enable_tool_calling: Включить ли вызов инструмента
            max_tool_iterations: Максимальное количество итераций вызова инструмента."""
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            config=config,
            tool_registry=tool_registry,
            enable_tool_calling=enable_tool_calling,
            max_tool_iterations=max_tool_iterations,
        )

        # Проверьте, поддерживаются ли вызовы инструментов потоковой передачи

        self._supports_streaming_tools = isinstance(llm, EnhancedHelloAgentsLLM)

    async def arun_stream_with_tools(
        self,
        input_text: str,
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """Асинхронная потоковая операция (поддерживает вызов инструментов)

        Используйте метод astream_invoke_with_tools класса EnhancedHelloAgentsLLM для реализации элегантного вызова инструмента потоковой передачи.

        Аргументы:
            input_text: ввод пользователя
            **kwargs: другие параметры

        Выход:
            StreamEvent: событие потоковой передачи"""
        session_start_time = datetime.now()

        # Отправить стартовое событие

        yield StreamEvent.create(
            StreamEventType.AGENT_START,
            self.name,
            input_text=input_text
        )

        print(f"\n🤖 {self.name} начало处理问题（потоковый）: {input_text}")

        try:
            # Создать список сообщений

            messages = self._build_messages(input_text)

            # Проверьте, есть ли инструменты

            if not self.enable_tool_calling or not self.tool_registry:
                # Режим чистого диалога с использованием методов базового класса

                async for event in self._stream_without_tools(messages, **kwargs):
                    yield event
                return

            # Проверьте, поддерживает ли LLM вызовы инструментов потоковой передачи.

            if not self._supports_streaming_tools:
                import warnings
                warnings.warn(
«В настоящее время LLM не поддерживает вызовы инструментов потоковой передачи, он будет использовать режим без потоковой передачи».
                    "推荐使用 EnhancedHelloAgentsLLM 以获得更好的体验。",
                    UserWarning
                )
                # Возврат к непотоковому режиму базового класса

                response = self.run(input_text, **kwargs)
                yield StreamEvent.create(
                    StreamEventType.AGENT_FINISH,
                    self.name,
                    result=response
                )
                return

            # === Режим вызова инструмента потоковой передачи ===

            tool_schemas = self._build_tool_schemas()
print(f"🔧 ужевключитьинструмент调用，可用инструмент: {list(self.tool_registry._tools.keys())}")

            current_iteration = 0
            final_response = ""
            # Сбор записей вызовов инструментов (используется для хранения сеансов)

            tool_call_records: List[Dict[str, Any]] = []

            while current_iteration < self.max_tool_iterations:
                current_iteration += 1

                # Отправить событие начала шага

                yield StreamEvent.create(
                    StreamEventType.STEP_START,
                    self.name,
                    step=current_iteration,
                    max_steps=self.max_tool_iterations
                )

                print(f"\n--- 第 {current_iteration} 轮 ---")
                print("💭 LLM вывод: ", end="", flush=True)

                # Вызов методов с использованием инструментов потоковой передачи LLM

                try:
                    async for event in self.llm.astream_invoke_with_tools(
                        messages=messages,
                        tools=tool_schemas,
                        tool_choice="auto",
                        **kwargs
                    ):
                        # Обрабатывать текстовый контент

                        if event.event_type == StreamToolEventType.CONTENT:
                            yield StreamEvent.create(
                                StreamEventType.LLM_CHUNK,
                                self.name,
                                chunk=event.content,
                                step=current_iteration
                            )
                            print(event.content, end="", flush=True)

                        # Начинается вызов инструмента (печатает информацию, не отправляет события)

                        elif event.event_type == StreamToolEventType.TOOL_CALL_START:
                            pass  # Прежде чем отправлять событие, дождитесь завершения вызова инструмента.


                    print()  # новая строка


                except Exception as e:
                    error_msg = f"LLM 调用ошибка: {str(e)}"
                    print(f"\n❌ {error_msg}")
                    yield StreamEvent.create(
                        StreamEventType.ERROR,
                        self.name,
                        error=error_msg
                    )
                    break

                # Получите совокупные результаты

                result = self.llm.get_last_stream_tool_result()
                if result is None:
                    break

                # Проверьте, есть ли вызов инструмента

                complete_tool_calls = result.get_complete_tool_calls()

                # Независимо от того, происходит ли вызов инструмента, текстовое содержимое этого раунда сохраняется.

                if result.content:
                    final_response = result.content

                if not complete_tool_calls:
                    # Без вызова инструмента, возврат напрямую

                    if not final_response:
                        final_response = "Извините, я не могу ответить на этот вопрос。"
                    # Показать предварительный просмотр контента

                    preview = final_response[:100] + "..." if len(final_response) > 100 else final_response
print(f"💬 Прямой ответ: {preview}")
                    break

print(f"🔧 Подготовьте выбор {len(complete_tool_calls)} вызовов инструментов...")

                # Добавить сообщение помощника в историю

                messages.append(result.to_assistant_message())

                # Выполнить все вызовы инструментов

                for tc in complete_tool_calls:
                    tool_name = tc["name"]
                    tool_call_id = tc["id"]

                    try:
                        arguments = json.loads(tc["arguments"])
                    except json.JSONDecodeError as e:
                        print(f"❌ инструмент参数解析ошибка: {e}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"Ошибка：参数格式不正确 - {str(e)}"
                        })
                        continue

                    print(f"🎬 Вызов инструмента: {tool_name}({arguments})")

                    # Отправить событие начала вызова инструмента

                    yield StreamEvent.create(
                        StreamEventType.TOOL_CALL_START,
                        self.name,
                        tool_name=tool_name,
                        tool_call_id=tool_call_id,
                        args=arguments
                    )

                    # Контролируйте доходность и убедитесь, что SSE отправляет событиеtool_start.

                    await asyncio.sleep(0)

                    # Инструмент выполнения

                    exec_result = self._execute_tool_call(tool_name, arguments)

                    # Усеченное отображение

                    result_preview = exec_result[:200] + "..." if len(exec_result) > 200 else exec_result
                    if exec_result.startswith("❌"):
                        print(f"❌ инструментвыполнитьошибка: {result_preview}")
                    else:
                        print(f"👀 观察: {result_preview}")

                    # Отправить событие завершения вызова инструмента

                    yield StreamEvent.create(
                        StreamEventType.TOOL_CALL_FINISH,
                        self.name,
                        tool_name=tool_name,
                        tool_call_id=tool_call_id,
                        result=exec_result
                    )

                    # Запись вызовов инструментов (для сохранения сеансов)

                    tool_call_records.append({
                        "name": tool_name,
                        "args": arguments,
                        "result": exec_result,
                        "status": "error" if exec_result.startswith("❌") else "done"
                    })

                    # Добавить результаты инструмента в сообщение

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": exec_result
                    })

                # Отправить событие завершения шага

                yield StreamEvent.create(
                    StreamEventType.STEP_FINISH,
                    self.name,
                    step=current_iteration
                )

            # Если максимальное количество итераций превышено, получить последний ответ

            if current_iteration >= self.max_tool_iterations and not final_response:
print("⏰ужедостигнуто максимальное количество итераций и получен окончательный ответ...")

                try:
                    async for chunk in self.llm.astream_invoke(messages, **kwargs):
                        final_response += chunk
                        yield StreamEvent.create(
                            StreamEventType.LLM_CHUNK,
                            self.name,
                            chunk=chunk
                        )
                        print(chunk, end="", flush=True)
                    print()
                except Exception as e:
print(f"❌ Окончательный ответошибка: {e}")
                    result = self.llm.get_last_stream_tool_result()
                    final_response = result.content if result else "Извините, я не могу ответить на этот вопрос。"

            # Сохранить в историю (в формате спецификации OpenAI)

            self.add_message(Message(input_text, "user"))

            # Если есть вызов инструмента, сохраните сообщение о вызове инструмента.

            if tool_call_records:
                # Сохранять сообщения помощника (включаяtool_calls)

                tool_calls_for_message = [
                    {
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"])
                        }
                    }
                    for i, tc in enumerate(tool_call_records)
                ]
                self.add_message(Message(
                    "",  # При вызове инструмента может отсутствовать текстовое содержимое.

                    "assistant",
                    metadata={"tool_calls": tool_calls_for_message}
                ))

                # Сохраняйте каждое сообщение инструмента

                for i, tc in enumerate(tool_call_records):
                    self.add_message(Message(
                        tc["result"],
                        "tool",
                        metadata={"tool_call_id": f"call_{i}"}
                    ))

            # Сохранить окончательный ответ помощника

            if final_response:
                self.add_message(Message(final_response, "assistant"))

            duration = (datetime.now() - session_start_time).total_seconds()
print(f"\nвещество завершено, потребовалось {duration:.2f} с, всего {current_iteration} раундов")

            # Отправить событие завершения

            yield StreamEvent.create(
                StreamEventType.AGENT_FINISH,
                self.name,
                result=final_response
            )

        except Exception as e:
            print(f"❌ Agent выполнитьошибка: {e}")
            yield StreamEvent.create(
                StreamEventType.ERROR,
                self.name,
                error=str(e),
                error_type=type(e).__name__
            )
            # Не повышайте, убедитесь, что ответ потоковой передачи завершается нормально

            # Отправьте событие завершения, чтобы оно завершилось корректно

            yield StreamEvent.create(
                StreamEventType.AGENT_FINISH,
                self.name,
                result=""  # Пустой результат указывает на неудачу

            )

    async def _stream_without_tools(
        self,
        messages: List[Dict],
        **kwargs
    ) -> AsyncGenerator[StreamEvent, None]:
        """Режим чистого разговора (без вызовов инструментов)"""
print("📝 Режим чистого разговора (без вызова инструмента)")

        full_response = ""
        async for chunk in self.llm.astream_invoke(messages, **kwargs):
            full_response += chunk
            yield StreamEvent.create(
                StreamEventType.LLM_CHUNK,
                self.name,
                chunk=chunk
            )
            print(chunk, end="", flush=True)

        print()

        # сохранить историю

        self.add_message(Message(messages[-1]["content"], "user"))
        self.add_message(Message(full_response, "assistant"))

print(f"💬 回复завершено")

        yield StreamEvent.create(
            StreamEventType.AGENT_FINISH,
            self.name,
            result=full_response
        )
