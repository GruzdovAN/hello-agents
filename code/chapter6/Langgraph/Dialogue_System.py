"""
Intelligent Search Assistant — Настоящая поисковая система на основе LangGraph + Tavily API
1. Понять потребности пользователей
2. Используйте Tavily API для полноценного поиска информации.
3. Генерируйте ответы на основе результатов поиска.
"""

import asyncio
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Загрузить переменные среды
load_dotenv()

# Определить государственную структуру
class SearchState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str        # Пользовательский запрос
    search_query: str      # Оптимизированный поисковый запрос
    search_results: str    # Результаты поиска Тавили
    final_answer: str      # окончательный ответ
    step: str             # текущий шаг

# Инициализируйте модель и клиент Tavily.
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID", "gpt-4o-mini"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    temperature=0.7
)

# Инициализировать клиент Tavily
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def understand_query_node(state: SearchState) -> SearchState:
    """Шаг 1. Изучите запросы пользователей и сгенерируйте ключевые слова для поиска."""
    
    # Получайте последние новости пользователей
    user_message = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    understand_prompt = f"""Проанализируйте запрос пользователя: "{user_message}"

Пожалуйста, выполните два задания:
1. Кратко изложите то, что хотят знать пользователи.
2. Создайте ключевые слова, наиболее подходящие для поиска (допускаются как китайские, так и английские слова, но они должны быть точными).

Формат:
Понимание: [Краткий обзор потребностей пользователей]
Условия поиска: [Лучшие ключевые слова для поиска]"""

    response = llm.invoke([SystemMessage(content=understand_prompt)])
    
    # Извлечение ключевых слов для поиска
    response_text = response.content
    search_query = user_message  # Использовать необработанный запрос по умолчанию
    
    if "Условия поиска:" in response_text:
        search_query = response_text.split("Условия поиска:")[1].strip()
    elif "Ключевые слова для поиска:" in response_text:
        search_query = response_text.split("Ключевые слова для поиска:")[1].strip()
    
    return {
        "user_query": response.content,
        "search_query": search_query,
        "step": "understood",
        "messages": [AIMessage(content=f"Я понимаю ваши потребности: {response.content}")]
    }

def tavily_search_node(state: SearchState) -> SearchState:
    """Шаг 2. Используйте API Tavily для реального поиска."""
    
    search_query = state["search_query"]
    
    try:
        print(f"🔍 Ищем: {search_query}")
        
        # Вызов API поиска Тавили
        response = tavily_client.search(
            query=search_query,
            search_depth="basic",
            include_answer=True,
            include_raw_content=False,
            max_results=5
        )
        
        # Обработка результатов поиска
        search_results = ""
        
        # Отдавайте предпочтение исчерпывающим ответам Тавили
        if response.get("answer"):
            search_results = f"Исчерпывающий ответ:\n{response['ответ']}\n\n"
        
        # Добавить конкретные результаты поиска
        if response.get("results"):
            search_results += "Сопутствующая информация:\n"
            for i, result in enumerate(response["results"][:3], 1):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                search_results += f"{я}. {title}\n{content}\nИсточник: {url}\n\n"
        
        if not search_results:
            search_results = "К сожалению, релевантной информации не найдено."
        
        return {
            "search_results": search_results,
            "step": "searched",
            "messages": [AIMessage(content=f"✅ Поиск завершен! Нашли нужную информацию и разбираем для вас ответы...")]
        }
        
    except Exception as e:
        error_msg = f"Произошла ошибка при поиске: {str(e)}"
        print(f"❌ {error_msg}")
        
        return {
            "search_results": f"Поиск не удался: {error_msg}",
            "step": "search_failed",
            "messages": [AIMessage(content="❌ Если при поиске вы столкнетесь с проблемой, я отвечу вам на нее, исходя из имеющихся у меня знаний.")]
        }

def generate_answer_node(state: SearchState) -> SearchState:
    """Шаг 3. Создайте окончательный ответ на основе результатов поиска."""
    
    # Проверьте, есть ли результаты поиска
    if state["step"] == "search_failed":
        # Если поиск не удался, ответьте на основе знаний LLM
        fallback_prompt = f"""API поиска временно недоступен. Пожалуйста, ответьте на вопросы пользователей, исходя из своих знаний:

Вопрос пользователя: {state['user_query']}

Пожалуйста, дайте полезный ответ и объясните, что он основан на предварительных знаниях."""
        
        response = llm.invoke([SystemMessage(content=fallback_prompt)])
        
        return {
            "final_answer": response.content,
            "step": "completed",
            "messages": [AIMessage(content=response.content)]
        }
    
    # Генерируйте ответы на основе результатов поиска
    answer_prompt = f"""Предоставляйте пользователям полные и точные ответы на основе следующих результатов поиска:

Вопрос пользователя: {state['user_query']}

Результаты поиска:
{состояние['search_results']}

Пожалуйста, запросите:
1. Комплексные результаты поиска и предоставление точных и полезных ответов.
2. Если это техническая проблема, предоставьте конкретные решения или код.
3. Укажите источники важной информации.
4. Ответы должны быть четко структурированы и понятны.
5. Если результаты поиска недостаточно полны, объясните и предоставьте дополнительные предложения."""

    response = llm.invoke([SystemMessage(content=answer_prompt)])
    
    return {
        "final_answer": response.content,
        "step": "completed",
        "messages": [AIMessage(content=response.content)]
    }

# Создайте рабочий процесс поиска
def create_search_assistant():
    workflow = StateGraph(SearchState)
    
    # Добавьте три узла
    workflow.add_node("understand", understand_query_node)
    workflow.add_node("search", tavily_search_node)
    workflow.add_node("answer", generate_answer_node)
    
    # Настройте линейный процесс
    workflow.add_edge(START, "understand")
    workflow.add_edge("understand", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", END)
    
    # Компилировать график
    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

async def main():
    """Основная функция: запуск интеллектуального помощника поиска."""
    
    # Проверьте ключ API
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ Ошибка: настройте TAVILY_API_KEY в файле .env.")
        return
    
    app = create_search_assistant()
    
    print("🔍 Запущен умный помощник по поиску!")
    print("Я буду использовать API Tavily для поиска самой последней и точной информации для вас.")
    print("Поддерживает различные вопросы: новости, технологии, мелочи и многое другое.")
    print("(Введите «quit», чтобы выйти)\n")
    
    session_count = 0
    
    while True:
        user_input = input("🤔 Что вы хотите знать: ").strip()
        
        if user_input.lower() in ['quit', 'q', 'покидать', 'exit']:
            print("Спасибо за использование! до свидания! 👋")
            break
        
        if not user_input:
            continue
        
        session_count += 1
        config = {"configurable": {"thread_id": f"search-session-{session_count}"}}
        
        # исходное состояние
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": "",
            "search_query": "",
            "search_results": "",
            "final_answer": "",
            "step": "start"
        }
        
        try:
            print("\n" + "="*60)
            
            # Выполнить рабочий процесс
            async for output in app.astream(initial_state, config=config):
                for node_name, node_output in output.items():
                    if "messages" in node_output and node_output["messages"]:
                        latest_message = node_output["messages"][-1]
                        if isinstance(latest_message, AIMessage):
                            if node_name == "understand":
                                print(f"🧠 Стадия понимания: {latest_message.content}")
                            elif node_name == "search":
                                print(f"🔍 Фаза поиска: {latest_message.content}")
                            elif node_name == "answer":
                                print(f"\n💡 Окончательный ответ:\n{latest_message.content}")
            
            print("\n" + "="*60 + "\n")
        
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")
            print("Пожалуйста, введите свой вопрос еще раз. \п")

if __name__ == "__main__":
    asyncio.run(main())