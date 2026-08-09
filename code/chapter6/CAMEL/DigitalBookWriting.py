from colorama import Fore
from camel.societies import RolePlaying
from camel.utils import print_text_animated
from camel.models import ModelFactory
from camel.types import ModelPlatformType
from dotenv import load_dotenv
import os

load_dotenv()
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

#Создайте модель, взяв в качестве примера Qwen, вызвав API платформы больших моделей Bailian.
model = ModelFactory.create(
    model_platform=ModelPlatformType.QWEN,
    model_type=LLM_MODEL,
    url=LLM_BASE_URL,
    api_key=LLM_API_KEY
)

# Определить задачи совместной работы
task_prompt = """
Создайте короткую электронную книгу «Психология прокрастинации», предназначенную для широкой публики, интересующейся психологией.
Требования:
1. Содержание научное и строгое, основанное на эмпирических исследованиях.
2. Язык прост для понимания и позволяет избежать слишком большого количества технических терминов.
3. Содержит практические предложения по улучшению и тематические исследования.
4. Объем следует контролировать на уровне 8 000–10 000 слов.
5. Четкая структура, включая введение, основные главы и резюме.
"""

print(Fore.YELLOW + f"Совместная задача:\n{task_prompt}\n")

# Инициализация сеанса ролевой игры
role_play_session = RolePlaying(
    assistant_role_name="психолог", 
    user_role_name="писатель", 
    task_prompt=task_prompt,
    model=model
)

print(Fore.CYAN + f"Описание конкретной задачи:\n{role_play_session.task_prompt}\n")

# Начать совместную беседу
chat_turn_limit, n = 30, 0
input_msg = role_play_session.init_chat()

while n < chat_turn_limit:
    n += 1
    assistant_response, user_response = role_play_session.step(input_msg)
    
    print_text_animated(Fore.BLUE + f"Автор:\n\n{user_response.msg.content}\n")
    print_text_animated(Fore.GREEN + f"Психолог:\n\n{assistant_response.msg.content}\n")
    
    # Проверить флаг завершения задачи
    if "CAMEL_TASK_DONE" in user_response.msg.content:
        print(Fore.MAGENTA + "✅ Создание электронной книги завершено!")
        break
    
    input_msg = assistant_response.msg

print(Fore.YELLOW + f"Всего было проведено {n} раундов совместных бесед.")