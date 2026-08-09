"""
10.3.3 Использование инструмента HelloAgents A2A
(1) Создайте сервер агента A2A.
"""

from hello_agents.protocols import A2AServer
import threading
import time

# Создать службу агента-исследователя
researcher = A2AServer(
    name="researcher",
    description="Агент, ответственный за поиск и анализ информации",
    version="1.0.0"
)

# Определить навыки
@researcher.skill("research")
def handle_research(text: str) -> str:
    """Обрабатывать запросы на исследования"""
    import re
    match = re.search(r'research\s+(.+)', text, re.IGNORECASE)
    topic = match.group(1).strip() if match else text
    
    # Фактическая логика исследования (упрощенная здесь)
    result = {
        "topic": topic,
        "findings": f"Результаты исследования по {теме}...",
        "sources": ["Источник 1", "Источник 2", "Источник 3"]
    }
    return str(result)

# Запустить службу в фоновом режиме
def start_server():
    researcher.run(host="localhost", port=5000)

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    print("✅ Служба агента исследователя запущена по адресу http://localhost:5000.")
    
    # Продолжайте работу программы
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nСлужба остановлена")

