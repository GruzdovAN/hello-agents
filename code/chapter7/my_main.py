# my_main.py
from dotenv import load_dotenv
from my_llm import MyLLM # Примечание. Импортируйте сюда наш собственный класс.

# Загрузить переменные среды
load_dotenv()

# Создайте экземпляр нашего переписанного клиента и укажите поставщика
llm = MyLLM(provider="modelscope") 

# Подготовить сообщение
messages = [{"role": "user", "content": "Здравствуйте, представьтесь, пожалуйста."}]

# Initiate call, think и другие методы унаследованы от родительского класса и не требуют переписывания.
response_stream = llm.think(messages)

# Распечатать ответ
print("ModelScope Response:")
for chunk in response_stream:
    # Чанк был напечатан один раз в библиотеке my_llm. Вам нужно только пройти здесь.
    # print(chunk, end="", flush=True)
    pass