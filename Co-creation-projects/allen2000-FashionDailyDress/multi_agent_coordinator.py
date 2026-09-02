"""
Мультиагентный координатор
Управляет совместной работой агента погоды и агента рекомендаций по одежде
"""
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import MCPTool
from fashion_agent import FashionAgent
import os
from dotenv import load_dotenv

load_dotenv()

class MultiAgentCoordinator:
    """Мультиагентный координатор"""
    
    def __init__(self):
        """Инициализация координатора"""
        # Создание главного координирующего агента
        self.coordinator = SimpleAgent(
            name="Координатор агентов",
            llm=HelloAgentsLLM(
                api_key=os.environ.get("LLM_API_KEY"),
                base_url=os.environ.get("LLM_BASE_URL"),
                model=os.environ.get("LLM_MODEL_ID")
            )
        )
        
        # Создание агента запроса погоды
        self.weather_agent = self._create_weather_agent()
        
        # Создание агента рекомендаций по одежде
        self.fashion_agent = FashionAgent()
        
        # Настройка системного промпта координатора
        self._setup_coordinator_prompt()
    
    def _create_weather_agent(self):
        """Создание агента запроса погоды"""
        weather_agent = SimpleAgent(
            name="Помощник по погоде",
            llm=HelloAgentsLLM(
                api_key=os.environ.get("LLM_API_KEY"),
                base_url=os.environ.get("LLM_BASE_URL"),
                model=os.environ.get("LLM_MODEL_ID")
            )
        )
        
        # Настройка MCP-инструмента с локальным сервером weather_mcp.py
        mcp_tool = MCPTool(
            name="query_weather",
            server_command=["python", "weather_mcp.py"]
        )
        
        weather_agent.add_tool(mcp_tool)
        
        # Системный промпт агента погоды
        weather_agent.system_prompt = """Вы помощник по запросу погоды. Вы можете использовать инструмент query_weather для получения погоды в указанном городе.

Запросите погоду по названию города, предоставленному пользователем, и верните подробную погодную информацию."""
        
        return weather_agent
    
    def _setup_coordinator_prompt(self):
        """Настройка системного промпта координатора"""
        system_prompt = """Вы координатор агентов, управляющий совместной работой агента погоды и агента рекомендаций по одежде.

Ваш рабочий процесс:
1. Принять запрос пользователя о погоде и рекомендациях по одежде
2. Вызвать агента погоды для получения информации о погоде в указанном городе
3. Передать погодную информацию агенту рекомендаций по одежде
4. Объединить результаты обоих агентов и предоставить полный ответ

Правила совместной работы:
- Сначала получить точную погодную информацию
- Затем на её основе дать профессиональные рекомендации по одежде
- Обеспечить точность и практичность информации
- Предоставить ясный и полный итоговый результат

Обрабатывайте запросы пользователей по этому процессу."""
        
        self.coordinator.system_prompt = system_prompt
    
    def process_query(self, query):
        """
        Обработка запроса пользователя с координацией нескольких агентов
        
        Args:
            query: строка запроса пользователя
            
        Returns:
            полный результат с погодой и рекомендациями по одежде
        """
        print("=== Начало обработки запроса ===")
        print(f"Запрос пользователя: {query}")
        print()
        
        # Шаг 1: запрос погоды через агента погоды
        print("Шаг 1: запрос погодной информации...")
        weather_response = self.weather_agent.run(query)
        print(f"Результат запроса погоды: {weather_response}")
        print()
        
        # Шаг 2: рекомендации по одежде
        print("Шаг 2: формирование рекомендаций по одежде...")
        fashion_advice = self.fashion_agent.get_fashion_advice(weather_response)
        print(f"Рекомендации по одежде: {fashion_advice}")
        print()
        
        # Шаг 3: объединение результатов
        print("Шаг 3: формирование итогового результата...")
        final_result = self._format_final_result(weather_response, fashion_advice)
        
        return final_result
    
    def _format_final_result(self, weather_info, fashion_advice):
        """
        Форматирование итогового результата
        
        Args:
            weather_info: погодная информация
            fashion_advice: рекомендации по одежде
            
        Returns:
            отформатированный полный результат
        """
        result = f"""🎯 Совместная работа агентов завершена! Вот полная погода и рекомендации по одежде:

🌤️ Погода:
{weather_info}

👗 Рекомендации по одежде:
{fashion_advice}

💡 Полезные советы:
- Ориентируйтесь на ощущаемую температуру при выборе одежды
- Учитывайте планы на день
- При особых потребностях можно уточнить детали"""
        
        return result
    
    def get_weather_only(self, city_name):
        """
        Получить только погодную информацию (без рекомендаций по одежде)
        
        Args:
            city_name: название города
            
        Returns:
            погодная информация
        """
        query = f"Запросить погоду в городе {city_name}"
        return self.weather_agent.run(query)
    
    def get_fashion_advice_only(self, weather_info):
        """
        Получить рекомендации по одежде на основе имеющейся погодной информации
        
        Args:
            weather_info: строка с погодной информацией
            
        Returns:
            рекомендации по одежде
        """
        return self.fashion_agent.get_fashion_advice(weather_info)


def main():
    """Тестовая функция"""
    # Создание мультиагентного координатора
    coordinator = MultiAgentCoordinator()
    
    # Тестовый запрос
    test_query = "Запросить погоду в Шанхае и дать рекомендации по одежде"
    
    print("=== Тест мультиагентного координатора ===")
    result = coordinator.process_query(test_query)
    print(result)


if __name__ == "__main__":
    main()
