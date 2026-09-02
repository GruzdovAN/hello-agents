"""
Агент базы данных — интеллектуальный помощник по запросам на базе ReAct.
"""
import re
from typing import Optional, List
from hello_agents import ReActAgent, HelloAgentsLLM, Config, Message, ToolRegistry
from tools import OracleQueryTool, SQLGeneratorTool, format_query_result
from config import DatabaseConfig


DATABASE_AGENT_PROMPT = """Вы — профессиональный помощник по запросам к базе данных. Понимаете запросы на естественном языке, преобразуете их в SQL, получаете данные из Oracle и форматируете вывод.

## Доступные инструменты
{tools}

## Рабочий процесс
Отвечайте строго в формате:

Thought: ваш ход мысли, анализ запроса и план следующего шага.
Action: одно из:
- `{{tool_name}}[{{tool_input}}]` — вызов инструмента
- `Finish[финальный ответ]` — когда информации достаточно

## Руководство
1. При запросе пользователя сначала GetSchema — структура таблиц
2. GenerateSQL — естественный язык → SQL
3. ExecuteQuery — выполнение SQL и результат

## Текущая задача
**Question:** {question}

## История выполнения
{history}

Начинайте рассуждение и действие:
"""


class DatabaseAgent(ReActAgent):
    """Агент запросов к БД"""
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        db_config: DatabaseConfig,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5
    ):
        super().__init__(name, llm, system_prompt, config)
        
        self.db_config = db_config
        self.max_steps = max_steps
        self.current_history: List[str] = []
        self.prompt_template = DATABASE_AGENT_PROMPT
        
        self.oracle_tool = OracleQueryTool(db_config)
        self.sql_generator = SQLGeneratorTool(llm)
        
        self.tool_registry = ToolRegistry()
        self.tool_registry.register_function(
            "GetSchema",
            "Схема БД: имена таблиц и поля.",
            self._get_schema
        )
        self.tool_registry.register_function(
            "GenerateSQL",
            "Преобразование запроса на естественном языке в SQL Oracle.",
            self._generate_sql
        )
        self.tool_registry.register_function(
            "ExecuteQuery",
            "Выполнение SQL и возврат результата.",
            self._execute_query
        )
        
        self.schema_cache = None
        print(f"✅ {name} инициализирован, макс. шагов: {max_steps}")
    
    def _get_schema(self, input_text: str) -> str:
        """Схема БД: таблицы и поля."""
        schema_info = self.oracle_tool.get_schema_info()
        self.schema_cache = schema_info
        return schema_info
    
    def _generate_sql(self, input_text: str) -> str:
        """NL → SQL Oracle."""
        if not self.schema_cache:
            self.schema_cache = self.oracle_tool.get_schema_info()
        
        sql = self.sql_generator.generate_sql(input_text, self.schema_cache)
        
        is_valid, msg = self.sql_generator.validate_sql(sql)
        if not is_valid:
            return f"Ошибка генерации SQL: {msg}"
        
        return f"Сгенерированный SQL: {sql}"
    
    def _execute_query(self, input_text: str) -> str:
        """Выполнить SQL и вернуть результат."""
        sql = input_text.strip()
        
        if sql.startswith("Сгенерированный SQL: "):
            sql = sql.replace("Сгенерированный SQL: ", "")
        
        result = self.oracle_tool.execute_query(sql)
        
        if not result["success"]:
            return f"Ошибка выполнения запроса: {result['error']}"
        
        formatted_result = format_query_result(result)
        return formatted_result
    
    def run(self, input_text: str, **kwargs) -> str:
        """Запуск агента БД."""
        self.current_history = []
        current_step = 0
        
        print(f"\n🤖 {self.name} обрабатывает запрос: {input_text}")
        
        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- Шаг {current_step} ---")
            tools_desc = self.tool_registry.get_tools_description()
            history_str = "\n".join(self.current_history)
            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs)
            thought, action = self._parse_output(response_text)
            
            if thought:
                print(f"🤔 Мысль: {thought}")
            
            if action and action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                self.add_message(Message(input_text, "user"))
                self.add_message(Message(final_answer, "assistant"))
                return final_answer
            
            if action:
                tool_name, tool_input = self._parse_action(action)
                observation = self.tool_registry.execute_tool(tool_name, tool_input)
                print(f"🎬 Действие: {tool_name}[{tool_input}]")
                print(f"👀 Наблюдение: {observation}")
                self.current_history.append(f"Action: {action}")
                self.current_history.append(f"Observation: {observation}")
        
        final_answer = "Не удалось выполнить задачу за отведённое число шагов."
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer
    
    def _parse_output(self, text: str):
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action
    
    def _parse_action(self, action_text: str):
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)
    
    def _parse_action_input(self, action_text: str):
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""
