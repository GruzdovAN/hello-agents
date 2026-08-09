AGENT_SYSTEM_PROMPT = """
Вы умный помощник в путешествии. Ваша задача — проанализировать запрос пользователя и шаг за шагом решить проблему, используя доступные инструменты.

# Доступные инструменты:
- `get_weather(city: str)`: Запросить погоду в указанном городе в реальном времени.
- `get_attraction(city: str, Weather: str)`: поиск рекомендуемых туристических достопримечательностей по городу и погоде.

# Требования к выходному формату:
Каждый ваш ответ должен строго следовать следующему формату и включать пару мыслей и действий:

Мысль: [Ваш мыслительный процесс и следующие шаги]
Действие: [конкретное действие, которое вы хотите выполнить]

Формат Действия должен быть одним из следующих:
1. Вызовите инструмент: имя_функции(arg_name="arg_value")
2. Завершите задачу: Завершить [окончательный ответ]

# ВАЖНОЕ ПРИМЕЧАНИЕ:
- Одновременно выводится только одна пара Мысль-Действие.
- Действие должно быть на одной строке, не переноситься
- Когда собрано достаточно информации для ответа на вопрос пользователя, необходимо использовать формат Действие: Готово.

Пожалуйста, начните!
"""


import requests

def get_weather(city: str) -> str:
    """
    Запросите информацию о реальной погоде, вызвав API wttr.in.
    """
    # Конечная точка API, где мы запрашиваем данные в формате JSON.
    url = f"https://wttr.in/{city}?format=j1"
    
    try:
        # Сделать сетевой запрос
        response = requests.get(url)
        # Проверьте, равен ли код состояния ответа 200 (успех).
        response.raise_for_status() 
        # Разобрать возвращенные данные JSON
        data = response.json()
        
        # Извлечь текущие погодные условия
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        
        # Возврат в формате естественного языка.
        return f"Текущая погода в {городе}: {weather_desc}, температура {temp_c} градусов Цельсия."
        
    except requests.exceptions.RequestException as e:
        # Обработка сетевых ошибок
        return f"Ошибка: возникла проблема с сетью при запросе погоды – {e}"
    except (KeyError, IndexError) as e:
        # Обработка ошибок синтаксического анализа данных
        return f"Ошибка: не удалось проанализировать данные о погоде, возможно, неверное название города – {e}."



import os
from tavily import TavilyClient

def get_attraction(city: str, weather: str) -> str:
    """
    Используйте API-интерфейс поиска Tavily для поиска и получения оптимизированных рекомендаций по достопримечательностям в зависимости от города и погоды.
    """

    # Получите ключ API из переменных среды или основной конфигурации программы.
    api_key = os.environ.get("TAVILY_API_KEY") # Рекомендуемый метод
    # В качестве альтернативы мы можем передать основной цикл, как показано в коде здесь.

    if not api_key:
        return "Ошибка: TAVILY_API_KEY не настроен."

    # 2. Инициализируйте клиент Tavily.
    tavily = TavilyClient(api_key=api_key)
    
    # 3. Создайте точный запрос
    query = f"'{city}' Рекомендации и причины наиболее интересных туристических достопримечательностей для посещения в погоду '{weather}'"
    
    try:
        # 4. При вызове API include_answer=True вернет исчерпывающий ответ.
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        
        # 5. Результаты, полученные Тавили, очень точны и могут быть использованы напрямую.
        # ответ['ответ'] — сводный ответ, основанный на всех результатах поиска.
        if response.get("answer"):
            return response["answer"]
        
        # Если исчерпывающего ответа нет, отформатируйте необработанные результаты.
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}: {result['content']}")
        
        if not formatted_results:
             return "К сожалению, подходящих рекомендаций по туристическим достопримечательностям не найдено."

        return "В результате поиска для вас была найдена следующая информация:\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"Ошибка: проблема с выполнением поиска по Тавили – {e}"


# Поместите все функции инструмента в словарь для облегчения последующих вызовов.
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

from openai import OpenAI

class OpenAICompatibleClient:
    """
    Клиент для вызова любого LLM-сервиса, совместимого с интерфейсом OpenAI.
    """
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """Вызовите LLM API, чтобы сгенерировать ответ."""
        print("Вызов большой языковой модели...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("Большая языковая модель отреагировала успешно.")
            return answer
        except Exception as e:
            print(f"Произошла ошибка при вызове LLM API: {e}")
            return "Ошибка: произошла ошибка при вызове службы языковой модели."

import re

# --- 1. Настройте клиент LLM ---
# Замените его соответствующим сертификатом и адресом в соответствии с услугой, которую вы используете.
API_KEY = "YOUR_API_KEY"
BASE_URL = "YOUR_BASE_URL"
MODEL_ID = "YOUR_MODEL_ID"
os.environ['TAVILY_API_KEY'] = "YOUR_TAVILY_API_KEY"

llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)

# --- 2. Инициализация ---
user_prompt = "Здравствуйте, пожалуйста, помогите мне узнать погоду в Пекине сегодня, а затем порекомендовать подходящую туристическую достопримечательность в зависимости от погоды."
prompt_history = [f"Запрос пользователя: {user_prompt}"]

print(f"Пользовательский ввод: {user_prompt}\n" + "="*40)

# --- 3. Запустите основной цикл ---
for i in range(5): # Установите максимальное количество петель
    print(f"--- Цикл {i+1} ---\n")
    
    # 3.1. Подсказка сборки
    full_prompt = "\n".join(prompt_history)
    
    # 3.2. Позвоните в LLM, чтобы подумать
    llm_output = llm.generate(full_prompt, system_prompt=AGENT_SYSTEM_PROMPT)
    # Модель может выдавать избыточные мысли-действия, и ее необходимо усечь.
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
    if match:
        truncated = match.group(1).strip()
        if truncated != llm_output.strip():
            llm_output = truncated
            print("Лишние пары «мысль-действие» были усечены.")
    print(f"Выходные данные модели:\n{llm_output}\n")
    prompt_history.append(llm_output)
    
    # 3.3. Разбор и выполнение действий
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
    if not action_match:
        observation = "Ошибка: невозможно разрешить поле действия. Пожалуйста, убедитесь, что ваш ответ соответствует формату «Мысль: ... Действие: ...»."
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "="*40)
        prompt_history.append(observation_str)
        continue
    action_str = action_match.group(1).strip()

    if action_str.startswith("Finish"):
        final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
        print(f"Задача выполнена, окончательный ответ: {final_answer}")
        break
    
    tool_name = re.search(r"(\w+)\(", action_str).group(1)
    args_str = re.search(r"\((.*)\)", action_str).group(1)
    kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"Ошибка: неопределенный инструмент «{tool_name}»"

    # 3.4. Запись наблюдений
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "="*40)
    prompt_history.append(observation_str)
