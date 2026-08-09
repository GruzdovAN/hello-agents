"""
10.3.4 Использование инструментов A2A в агентах
(3) Расширенное использование: переговоры между агентами.
"""

from hello_agents.protocols import A2AServer, A2AClient
import threading
import time

# Создайте двух агентов, с которыми необходимо договориться.
agent1 = A2AServer(
    name="agent1",
    description="Agent 1"
)

@agent1.skill("propose")
def handle_proposal(text: str) -> str:
    """Обрабатывать предложения по переговорам"""
    import re
    import json
    
    # Анализировать предложение
    match = re.search(r'propose\s+(.+)', text, re.IGNORECASE)
    proposal_str = match.group(1).strip() if match else text
    
    try:
        proposal = eval(proposal_str)
        task = proposal.get("task")
        deadline = proposal.get("deadline")
        
        # Оценить предложения
        if deadline >= 7:  # Это займет минимум 7 дней
            result = {"accepted": True, "message": "Принять предложение"}
        else:
            result = {
                "accepted": False,
                "message": "Время слишком туго",
                "counter_proposal": {"deadline": 7}
            }
        return str(result)
    except:
        return str({"accepted": False, "message": "Неверный формат предложения."})

agent2 = A2AServer(
    name="agent2",
    description="Agent 2"
)

@agent2.skill("negotiate")
def negotiate_task(text: str) -> str:
    """Начать переговоры"""
    import re
    
    # Разбираем задачи и сроки
    match = re.search(r'negotiate\s+task:(.+?)\s+deadline:(\d+)', text, re.IGNORECASE)
    if match:
        task = match.group(1).strip()
        deadline = int(match.group(2))
        
        # Отправить предложение агенту 1
        proposal = {"task": task, "deadline": deadline}
        return str({"status": "negotiating", "proposal": proposal})
    else:
        return str({"status": "error", "message": "Неверный запрос на переговоры"})

# Запустить службу
if __name__ == "__main__":
    threading.Thread(target=lambda: agent1.run(port=7000), daemon=True).start()
    threading.Thread(target=lambda: agent2.run(port=7001), daemon=True).start()
    time.sleep(2)
    
    # Тестовый процесс переговоров
    client1 = A2AClient("http://localhost:7000")
    client2 = A2AClient("http://localhost:7001")
    
    # Агент2 инициирует переговоры
    negotiation = client2.execute_skill("negotiate", "задача согласования: разработать новые функции срок: 5")
    print(f"Запрос переговоров: {negotiation.get('result')}")
    
    # Агент1 оценивает предложения
    proposal = client1.execute_skill("propose", "предложить {'задача': 'Разработка новых функций', 'срок': 5}")
    print(f"Оценка предложения: {proposal.get('result')}")
    
    # Поддерживайте работу служб
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nСлужба остановлена")

