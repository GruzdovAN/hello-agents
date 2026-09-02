from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
os.makedirs("recipes", exist_ok=True)


def parse_response(response):
    try:
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "```" in response:
            json_start = response.find("```") + 3
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "{" in response and "}" in response:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
        else:
поднять ValueError("Данные JSON не найдены в ответе")
        
        data = json.loads(json_str)
        return data
    except Exception as e:
print(f"⚠️ Не удалось проанализировать ответ: {str(e)}")
        return None


def write_content_to_file(content):
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # 例: 20260428_143022
    filename = f"recipes/recipes_{timestamp}.md" 

    with open(filename, "w", encoding="utf-8") as wf:
        wf.write(content)

print(f" ✅ Рецепт создан: {имя файла}")


web_search_tool = MCPTool(name="web_research", server_command=["npx", "-y", "@mzxrai/mcp-webresearch@latest"])


# =================================== Ассистент поиска рецептов =====================================
caipu_search_agent = SimpleAgent(
    name="caipu_search_agent",
    llm=HelloAgentsLLM(),
    system_prompt="""
Вы эксперт по поиску рецептов. Ваша задача — поиск подходящих рецептов, исходя из потребностей и предпочтений пользователя.

**ВАЖНОЕ ПРИМЕЧАНИЕ:**
你必须使用工具来搜索菜谱!不要自己编造菜谱信息!返回的内容至少包括菜名和菜谱链接!可以包括菜品特点,便于后续筛选!

**Формат вызова инструмента:**
При использовании инструмента visit_page вы должны строго следовать следующему формату:
`[TOOL_CALL:visit_page:url=https://www.xiangha.com/so/?q=caipu&s=菜谱]`
`[TOOL_CALL:visit_page:url=https://www.xiangha.com/so/?q=caipu&s=食材]`


**Пример:**
Пользователь: «Ищите, как приготовить свиную грудинку»
Ваш ответ: [TOOL_CALL:visit_page:url=https://www.xiangha.com/so/?q=caipu&s=Свиная грудинка]

Пользователь: «Поиск рецептов, связанных с рыбой»
Ваш ответ: [TOOL_CALL:visit_page:url=https://www.xiangha.com/so/?q=caipu&s=鱼]

**Уведомление:**
1. Вы должны использовать инструменты, а не отвечать напрямую
2. 格式必须完全正确,包括方括号和冒号
3. Разделяйте параметры запятыми.
"""
)
caipu_search_agent.add_tool(web_search_tool)


def build_caipu_search_prompts(user_input):
return f"Вызовите инструмент visit_page, требования пользователя: {user_input}"


# =================================== Помощник эксперта по диете ======================================
caipu_select_agent = SimpleAgent(
    name="caipu_select_agent",
    llm=HelloAgentsLLM(),
    system_prompt="""
你是饮食专家。你的任务是根据用户需求和推荐的菜谱列表，为用户选择一个最合适的菜谱，并给出推荐理由。

**ВАЖНОЕ ПРИМЕЧАНИЕ:**
Вы должны выбирать из списка рекомендуемых рецептов, а новые названия блюд и ссылки на рецепты не могут быть созданы из воздуха.

Для возврата рекомендуемых рецептов строго следуйте следующему формату JSON:
```json
{
"name": "Тушеный карась",
  "url": "https://www.xiangha.com/caipu/102880489.html",
"reason": "**Причина рекомендации:**
- 🐟 **Приготовление на пару** — Самый легкий способ приготовления, меньше масла и соли.
- 🔥 **Подходит для снижения внутреннего жара** - Метод приготовления на пару не является острым или жирным и не усугубляет симптомы внутреннего жара.
- 💪 **Богат питательными веществами** - Окунь богат высококачественным белком, а мясо нежное и вкусное.
  "
}
```

Если подходящего результата рекомендации нет, верните пустые данные JSON в следующем формате:
```json
{

}
```
"""
)


def build_caipu_select_prompts(user_input, caipu_list):
    return f"用户需求: {user_input}，推荐的菜谱列表: {caipu_list}"


# =================================== Помощник по извлечению веб-контента =====================================
output_agent = SimpleAgent(
    name="demand_analyzer",
    llm=HelloAgentsLLM(),
    system_prompt="""
Вы являетесь экспертом в извлечении веб-контента. Ваша задача — вернуть окончательный полный рецепт на основе названия блюда и ссылки на рецепт, выбранных пользователем.

**ВАЖНОЕ ПРИМЕЧАНИЕ:**
Вы должны использовать инструменты, чтобы получить информацию о рецептах! Не выдумывайте информацию о рецептах самостоятельно!

**Формат вызова инструмента:**
При использовании инструмента visit_page вы должны строго следовать следующему формату:
`[TOOL_CALL:visit_page:url=ссылка на рецепт]`


**Пример:**
用户: 菜名: 红烧鲫鱼，菜谱链接: https://www.xiangha.com/caipu/102880489.html
Ваш ответ: [TOOL_CALL:visit_page:url=https://www.xiangha.com/caipu/102880489.html]

**Уведомление:**
1. Вы должны использовать инструменты, а не отвечать напрямую
2. 格式必须完全正确,包括方括号和冒号
3. Разделяйте параметры запятыми.
"""
)
output_agent.add_tool(web_search_tool)


def build_output_prompts(caipu_json):
    return f"菜名: {caipu_json['name']}, 菜谱链接: {caipu_json['url']}"


# =================================== Полный процесс =====================================

user_input = input("Пожалуйста, введите требования к рецепту (например: я хочу съесть раков) >>>")

print("\n\nИщем рецепты...")
search_caipu_result = caipu_search_agent.run(build_caipu_search_prompts(user_input=user_input))
print(search_caipu_result)

print("\n\nФильтрация рецептов...")
caipu_select_result = caipu_select_agent.run(build_caipu_select_prompts(user_input=user_input, caipu_list=search_caipu_result))
print(caipu_select_result)

print("\n\nРезультаты анализа...")
caipu_select_json = parse_response(caipu_select_result)
print(caipu_select_json)

if caipu_select_json:
print("\n\nГенерация рецептов...")
    output_result = output_agent.run(build_output_prompts(caipu_select_json))

print("\n\nСохраняем рецепт...")
print(f"Название блюда: {caipu_select_json['name']}\nПричина рекомендации: {caipu_select_json['reason']}")
    write_content_to_file(output_result)
else:
print("\n\nПодходящего рецепта не найдено")
