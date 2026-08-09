from hello_agents.protocols import ANPDiscovery, register_service

# Создайте центр обнаружения сервисов
discovery = ANPDiscovery()

# Регистрация агентского сервиса
register_service(
    discovery=discovery,
    service_id="nlp_agent_1",
    service_name="Эксперт по обработке НЛП А",
    service_type="nlp",
    capabilities=["text_analysis", "sentiment_analysis", "ner"],
    endpoint="http://localhost:8001",
    metadata={"load": 0.3, "price": 0.01, "version": "1.0.0"}
)

register_service(
    discovery=discovery,
    service_id="nlp_agent_2",
    service_name="Эксперт НЛП-процессинга B",
    service_type="nlp",
    capabilities=["text_analysis", "translation"],
    endpoint="http://localhost:8002",
    metadata={"load": 0.7, "price": 0.02, "version": "1.1.0"}
)

print("✅ Регистрация услуги завершена")

from hello_agents.protocols import discover_service

# Найти по типу
nlp_services = discover_service(discovery, service_type="nlp")
print(f"Найдено {len(nlp_services)} сервисов НЛП")

# Выбирайте сервис с наименьшей нагрузкой
best_service = min(nlp_services, key=lambda s: s.metadata.get("load", 1.0))
print(f"Лучший сервис: {best_service.service_name} (загрузка: {best_service.metadata['load']})")

from hello_agents.protocols import ANPNetwork

# Создать сеть
network = ANPNetwork(network_id="ai_cluster")

# Добавить узел
for service in discovery.list_all_services():
    network.add_node(service.service_id, service.endpoint)

# Установить соединение (подбирается в зависимости от возможностей)
network.connect_nodes("nlp_agent_1", "nlp_agent_2")

stats = network.get_network_stats()
print(f"✅ Строительство сети завершено, всего узлов: {stats['total_nodes']}")