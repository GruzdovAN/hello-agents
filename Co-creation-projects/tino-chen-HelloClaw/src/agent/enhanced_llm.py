"""Расширенная версия HelloAgentsLLM — поддерживает вызовы инструментов потоковой передачи."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Union, Any, AsyncIterator

from hello_agents.core.llm import HelloAgentsLLM
from hello_agents.core.exceptions import HelloAgentsException


# ==================== Структура данных вызова инструмента потоковой передачи ===================


class StreamToolEventType(Enum):
    """Тип события вызова инструмента потоковой передачи"""
    CONTENT = "content"  # Приращение текстового контента

    TOOL_CALL_START = "tool_call_start"  # Начинается вызов инструмента (получены идентификатор и имя)

    TOOL_CALL_DELTA = "tool_call_delta"  # Приращение параметра вызова инструмента

    FINISH = "finish"  # конец потока



@dataclass
class StreamToolEvent:
    """Событие вызова инструмента потоковой передачи

    Инкапсулируйте различные типы данных в потоковых ответах и унифицированно обрабатывайте текстовое содержимое и вызовы инструментов."""
    event_type: StreamToolEventType
    # текстовый контент

    content: Optional[str] = None
    # Вызов инструмента

    tool_call_index: Optional[int] = None  # Индекс вызова инструмента (для постепенного накопления)

    tool_call_id: Optional[str] = None  # Идентификатор вызова инструмента

    tool_name: Optional[str] = None  # Название инструмента

    tool_arguments_delta: Optional[str] = None  # Приращение параметра

    # последнее сообщение

    finish_reason: Optional[str] = None

    @property
    def is_content(self) -> bool:
        """Является ли это событием текстового контента"""
        return self.event_type == StreamToolEventType.CONTENT

    @property
    def is_tool_call(self) -> bool:
        """Вызывать ли событие для инструмента"""
        return self.event_type in (
            StreamToolEventType.TOOL_CALL_START,
            StreamToolEventType.TOOL_CALL_DELTA
        )

    @property
    def is_finish(self) -> bool:
        """Это конечное событие?"""
        return self.event_type == StreamToolEventType.FINISH


@dataclass
class StreamToolCallResult:
    """Результат после завершения вызова инструмента потоковой передачи

    Содержит совокупное текстовое содержимое и список вызовов инструментов."""
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    finish_reason: Optional[str] = None

    def add_content(self, delta: str):
        """Добавить текстовый контент"""
        self.content += delta

    def add_tool_call_start(self, index: int, tool_id: str, tool_name: str):
        """Добавить начало вызова инструмента"""
        # Убедитесь, что список достаточно длинный

        while len(self.tool_calls) <= index:
            self.tool_calls.append({"id": "", "name": "", "arguments": ""})
        self.tool_calls[index]["id"] = tool_id
        self.tool_calls[index]["name"] = tool_name

    def add_tool_call_delta(self, index: int, arguments_delta: str):
        """Добавить приращение параметра вызова инструмента"""
        while len(self.tool_calls) <= index:
            self.tool_calls.append({"id": "", "name": "", "arguments": ""})
        self.tool_calls[index]["arguments"] += arguments_delta

    def get_complete_tool_calls(self) -> List[Dict[str, Any]]:
        """Получить полный список вызовов инструментов (отфильтровать неполные)"""
        return [
            tc for tc in self.tool_calls
            if tc["id"] and tc["name"]
        ]

    def to_assistant_message(self) -> Dict[str, Any]:
        """Преобразование в формат сообщения помощника (для добавления в историю сообщений)"""
        message: Dict[str, Any] = {"role": "assistant", "content": self.content or None}
        if self.tool_calls:
            message["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                }
                for tc in self.get_complete_tool_calls()
            ]
        return message


# ==================== Расширенный класс LLM ====================


class EnhancedHelloAgentsLLM(HelloAgentsLLM):
    """Расширенная версия HelloAgentsLLM — добавлена поддержка потоковой передачи вызовов инструментов.

    Унаследованные от HelloAgentsLLM, добавлены следующие новые методы:
    - astream_invoke_with_tools: вызов инструмента асинхронной потоковой передачи.
    - get_last_stream_tool_result: получить совокупный результат последнего вызова инструмента потоковой передачи."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_stream_tool_result: Optional[StreamToolCallResult] = None

    async def astream_invoke_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        tool_choice: Union[str, Dict] = "auto",
        **kwargs
    ) -> AsyncIterator[StreamToolEvent]:
        """
        异步потоковый调用 LLM 并поддержкаинструмент调用（Function Calling）

        这是最优雅的потоковыйинструмент调用方法，封装了所有потоковый处理的复杂逻辑。

        Args:
            messages: сообщениесписок
            tools: инструмент schema список
tool_choice: стратегия выбора инструмента
            **kwargs: 其他参数（temperature, max_tokens 等）

        Yields:
            StreamToolEvent: потоковый事件，可能是文本содержимое或инструмент调用增量

        Example:
            async for event in llm.astream_invoke_with_tools(messages, tools):
                if event.is_content:
                    print(event.content, end="")
                elif event.event_type == StreamToolEventType.TOOL_CALL_START:
                    print(f"\\nВызов инструмента: {event.tool_name}")

            # 获取累积结果
            result = llm.get_last_stream_tool_result()
        """
        from openai import AsyncOpenAI

        # Создайте асинхронный клиент

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        # Параметры запроса сборки

        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "stream": True,
        }
        if kwargs.get("temperature") is not None:
            request_params["temperature"] = kwargs["temperature"]
        if self.max_tokens:
            request_params["max_tokens"] = self.max_tokens

        # Инициализировать накопленные результаты

        result = StreamToolCallResult()

        try:
            response = await client.chat.completions.create(**request_params)

            async for chunk in response:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # Обрабатывать текстовый контент

                if delta.content:
                    result.add_content(delta.content)
                    yield StreamToolEvent(
                        event_type=StreamToolEventType.CONTENT,
                        content=delta.content
                    )

                # Дельта вызова инструмента обработки

                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index

                        # Начался вызов инструмента (получен идентификатор или имя)

                        if tc_delta.id or (tc_delta.function and tc_delta.function.name):
                            tool_id = tc_delta.id or ""
                            tool_name = tc_delta.function.name if tc_delta.function else ""
                            if tool_id or tool_name:
                                result.add_tool_call_start(idx, tool_id, tool_name)
                                yield StreamToolEvent(
                                    event_type=StreamToolEventType.TOOL_CALL_START,
                                    tool_call_index=idx,
                                    tool_call_id=tool_id,
                                    tool_name=tool_name
                                )

                        # Приращение параметра вызова инструмента

                        if tc_delta.function and tc_delta.function.arguments:
                            args_delta = tc_delta.function.arguments
                            result.add_tool_call_delta(idx, args_delta)
                            yield StreamToolEvent(
                                event_type=StreamToolEventType.TOOL_CALL_DELTA,
                                tool_call_index=idx,
                                tool_arguments_delta=args_delta
                            )

                # Причина завершения обработки

                if choice.finish_reason:
                    result.finish_reason = choice.finish_reason
                    yield StreamToolEvent(
                        event_type=StreamToolEventType.FINISH,
                        finish_reason=choice.finish_reason
                    )

        except Exception as e:
raise HelloAgentsException(f"потоковыйинструмент调用ошибка: {str(e)}")

        # Сохраняйте совокупные результаты для дальнейшего использования.

        self._last_stream_tool_result = result

    def get_last_stream_tool_result(self) -> Optional[StreamToolCallResult]:
        """Получите совокупные результаты последнего вызова инструмента потоковой передачи.

        Возврат:
            StreamToolCallResult или нет"""
        return self._last_stream_tool_result
