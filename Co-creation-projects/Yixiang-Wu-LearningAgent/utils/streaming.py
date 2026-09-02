# utils/streaming.py
"""Функция инструмента потокового вывода"""

import sys
from typing import List
from hello_agents import HelloAgentsLLM


def should_stream(streaming: bool = None) -> bool:
    """
Определите, следует ли использовать потоковый вывод

    Args:
потоковая передача: заданные вручную настройки потокового вывода (Нет = определяется автоматически)

    Returns:
Использовать ли потоковый вывод
    """
    if streaming is None:
#Автоматическое обнаружение: интерактивный терминал использует потоковый вывод
        return sys.stdout.isatty()
    return streaming


def stream_response(llm: HelloAgentsLLM, messages: List[dict], silent: bool = False) -> str:
    """
Выполните потоковый вызов LLM и распечатайте результаты

    Args:
llm: экземпляр HelloAgentsLLM
сообщения: список сообщений LLM
бесшумный: использовать ли беззвучный режим (без вывода на печать)

    Returns:
полный текст ответа
    """
    full_response = ""
    previous_length = 0

    try:
        for chunk in llm.stream_invoke(messages):
# чанк является накопительным, печатается только новая часть
            if len(chunk) > previous_length:
                new_content = chunk[previous_length:]
                if not silent:
                    print(new_content, end='', flush=True)
                previous_length = len(chunk)

# Сохраняем полный ответ
            full_response = chunk

        if not silent:
print() # новая строка

        return full_response

    except Exception as e:
# Если потоковый вывод не удался, вернитесь к нормальному выводу
        if not silent:
print(f"\n[Ошибка потокового вывода, используйте обычный вывод: {e}]")
        return llm.invoke(messages)
