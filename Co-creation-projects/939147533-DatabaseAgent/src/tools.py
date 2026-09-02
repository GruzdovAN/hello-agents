"""
Набор инструментов для запросов к базе данных
"""
import oracledb
from typing import Dict, Any
from config import DatabaseConfig
from hello_agents import HelloAgentsLLM


class OracleQueryTool:
    """Инструмент запросов к Oracle-базе данных"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None
        
    def connect(self) -> bool:
        """Подключиться к Oracle-базе данных"""
        try:
            self.connection = oracledb.connect(
                user=self.config.username,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                service_name=self.config.service_name
            )
            return True
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return False
    
    def disconnect(self):
        """Отключиться от базы данных"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Выполнить SQL-запрос и вернуть результат"""
        if not self.connection:
            if not self.connect():
                return {"success": False, "error": "Не удалось подключиться к базе данных"}
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            
            cursor.close()
            
            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "sql": sql
            }
        except Exception as e:
            return {"success": False, "error": str(e), "sql": sql}
    
    def get_schema_info(self) -> str:
        """Получить информацию о структуре таблиц базы данных"""
        if not self.connection:
            if not self.connect():
                return "Не удалось подключиться к базе данных"
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            schema_info = []
            for table in tables:
                cursor.execute(f"""
                    SELECT column_name, data_type, nullable
                    FROM user_tab_columns
                    WHERE table_name = UPPER('{table}')
                    ORDER BY column_id
                """)
                columns = cursor.fetchall()
                
                col_desc = ", ".join([
                    f"{col[0]} ({col[1]})" 
                    for col in columns
                ])
                schema_info.append(f"Таблица {table}: {col_desc}")
            
            cursor.close()
            return "\n".join(schema_info)
        except Exception as e:
            return f"Ошибка получения структуры таблиц: {e}"


class SQLGeneratorTool:
    """Инструмент генерации SQL — LLM преобразует естественный язык в SQL"""
    
    def __init__(self, llm: HelloAgentsLLM):
        self.llm = llm
        self.system_prompt = """Ты профессиональный помощник по генерации SQL-запросов. Твоя задача — преобразовывать запросы пользователя на естественном языке в точные SQL-выражения для Oracle.

# Правила:
1. Возвращай только SQL-выражение, без пояснений и лишнего текста
2. Используй синтаксис Oracle SQL
3. Имена таблиц и полей — в верхнем регистре
4. Формат даты: 'YYYY-MM-DD'
5. Строки — в одинарных кавычках
6. Обеспечь безопасность SQL, избегай SQL-инъекций

# Структура таблиц базы данных:
{schema_info}

# Примеры:
Ввод пользователя: Получить информацию обо всех сотрудниках
Вывод: SELECT * FROM EMPLOYEES

Ввод пользователя: Найти сотрудников с зарплатой больше 5000
Вывод: SELECT * FROM EMPLOYEES WHERE SALARY > 5000

Теперь сгенерируй SQL по запросу пользователя на естественном языке.
"""
    
    def generate_sql(self, natural_query: str, schema_info: str) -> str:
        """Сгенерировать SQL-выражение"""
        prompt = self.system_prompt.format(schema_info=schema_info)
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": natural_query}
        ]
        
        response = self.llm.invoke(messages)
        
        sql = response.strip()
        
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
    
    def validate_sql(self, sql: str) -> tuple[bool, str]:
        """Проверить базовый синтаксис SQL-выражения"""
        sql_upper = sql.upper().strip()
        
        if not sql_upper.startswith(("SELECT", "WITH")):
            return False, "Разрешены только SELECT-запросы"
        
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE"]
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"Запрещено использовать оператор {keyword}"
        
        return True, "SQL-выражение прошло проверку"


def format_query_result(result: Dict[str, Any]) -> str:
    """Форматировать результат запроса в виде таблицы"""
    if not result["success"]:
        return f"Ошибка запроса: {result['error']}"
    
    if result["row_count"] == 0:
        return "Запрос выполнен успешно, но подходящих данных не найдено."
    
    columns = result["columns"]
    rows = result["rows"]
    
    col_widths = []
    for i, col in enumerate(columns):
        max_width = max(len(str(col)), max(len(str(row[i])) for row in rows))
        col_widths.append(max_width + 2)
    
    separator = "+" + "+".join("-" * width for width in col_widths) + "+"
    
    header = "|" + "|".join(
        str(col).center(width) for col, width in zip(columns, col_widths)
    ) + "|"
    
    data_rows = []
    for row in rows:
        data_row = "|" + "|".join(
            str(cell).center(width) for cell, width in zip(row, col_widths)
        ) + "|"
        data_rows.append(data_row)
    
    table = [separator, header, separator] + data_rows + [separator]
    
    return "\n".join(table)
