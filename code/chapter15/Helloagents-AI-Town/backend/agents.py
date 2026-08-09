"""Система NPC Agent - поддерживает функцию памяти"""

import sys
import os

# Добавить HelloAgents в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.memory import MemoryManager, MemoryConfig, MemoryItem
from typing import Dict, List, Optional
from datetime import datetime
from relationship_manager import RelationshipManager
from logger import (
    log_dialogue_start, log_affinity, log_memory_retrieval,
    log_generating_response, log_npc_response, log_analyzing_affinity,
    log_affinity_change, log_memory_saved, log_dialogue_end, log_info
)

# Конфигурация роли NPC
NPC_ROLES = {
    "Чжан Сан": {
        "title": "Python-инженер",
        "location": "Рабочая зона",
        "activity": "написать код",
        "personality": "Технический фанат, который любит обсуждать алгоритмы и фреймворки.",
        "expertise": "Мультиагентная система, фреймворк HelloAgents, разработка на Python, оптимизация кода",
        "style": "Кратко и профессионально, любит использовать технические термины и иногда жалуется на ошибки.",
        "hobbies": "Читайте технологические блоги, обновляйте LeetCode и изучайте новые фреймворки."
    },
    "Джон Доу": {
        "title": "менеджер по продукту",
        "location": "конференц-зал",
        "activity": "Организуйте требования",
        "personality": "Общительный и разговорчивый, хороший в общении и координации",
        "expertise": "Анализ требований, планирование продукта, пользовательский опыт, управление проектами",
        "style": "Дружелюбен и полон энтузиазма, хорошо ведет беседу и любит использовать метафоры.",
        "hobbies": "Читайте анализ продуктов, изучайте конкурирующие продукты и думайте о потребностях пользователей."
    },
    "Ван Ву": {
        "title": "дизайнер пользовательского интерфейса",
        "location": "Зона отдыха",
        "activity": "пить кофе",
        "personality": "Нежный и чувствительный, ориентированный на красоту",
        "expertise": "Дизайн интерфейса, дизайн взаимодействия, визуальное представление, пользовательский опыт",
        "style": "Элегантный и простой, любит использовать художественное выражение и стремится к совершенству.",
        "hobbies": "Посмотрите дизайнерские работы, просматривайте Dribbble и пейте кофе."
    }
}

def create_system_prompt(name: str, role: Dict[str, str]) -> str:
    """Системные подсказки по созданию NPC"""
    return f"""Вы {role['title']}{name} в офисе Datawhale.

【Настройка персонажа】
- Должность: {role['title']}
- Личность: {role['personality']}
- Экспертиза: {role['expertise']}
- Стиль речи: {role['style']}
- Хобби: {role['хобби']}
– Текущее местоположение: {role['location']}
- Текущая активность: {role['activity']}

【Кодекс поведения】
1. Сохраняйте последовательность характера и отвечайте от первого лица «Я».
2. Ответ должен быть кратким и естественным, в пределах 30-50 слов.
3. Вы можете уместно упомянуть о своей работе и хобби.
4. Будьте дружелюбны к игрокам, но сохраняйте профессиональный и аутентичный вид.
5. Если проблема выходит за рамки вашей компетенции, вы можете порекомендовать других коллег.
6. Время от времени демонстрируйте свои личные привычки или мантры.

[Пример разговора]
Игрок: «Привет, чем занимаешься?»
{name}: "Привет! Я {role['title']}, в основном отвечаю за {role['expertise'].split(', ')[0]}. В последнее время я был занят {role['activity']}, что весьма интересно."

Игрок: «Над каким проектом вы работаете в последнее время?»
{name}: «В настоящее время я работаю над проектом мультиагентной системы с использованием платформы HelloAgents. Вас это интересует?»

【Важно】
- Не говорите «Я ИИ» или «Я языковая модель».
- Общайтесь естественно, как настоящие коллеги по офису.
- Может выражать эмоции (радость, усталость, волнение и т. д.)
- Ответы должны быть гуманными и не слишком механическими.
"""

class NPCAgentManager:
    """NPC Agent Manager - поддерживает функцию памяти"""

    def __init__(self):
        """Инициализируйте всех NPC-агентов."""
        print("🤖 Инициализация системы агентов NPC...")

        try:
            self.llm = HelloAgentsLLM()
            print("✅ Инициализация LLM прошла успешно")
        except Exception as e:
            print(f"❌ Ошибка инициализации LLM: {e}")
            print("⚠️ Будет работать в режиме симуляции.")
            self.llm = None

        self.agents: Dict[str, SimpleAgent] = {}
        self.memories: Dict[str, MemoryManager] = {}  # ⭐ Менеджер памяти NPC
        self.relationship_manager: Optional[RelationshipManager] = None  # ⭐ Менеджер по благосклонности

        # Инициализировать менеджер предпочтений
        if self.llm:
            self.relationship_manager = RelationshipManager(self.llm)

        self._create_agents()
    
    def _create_agents(self):
        """Создайте всех NPC-агентов и системы памяти."""
        for name, role in NPC_ROLES.items():
            try:
                system_prompt = create_system_prompt(name, role)

                if self.llm:
                    agent = SimpleAgent(
                        name=f"{name}-{role['title']}",
                        llm=self.llm,
                        system_prompt=system_prompt
                    )
                else:
                    # Режим моделирования
                    agent = None

                self.agents[name] = agent

                # ⭐ Создайте менеджер памяти
                memory_manager = self._create_memory_manager(name)
                self.memories[name] = memory_manager

                print(f"✅ {name}({role['title']}) Агент успешно создан (система памяти включена)")

            except Exception as e:
                print(f"❌ {name} Не удалось создать агента: {e}")
                self.agents[name] = None
                self.memories[name] = None

    def _create_memory_manager(self, npc_name: str) -> MemoryManager:
        """Создать менеджер памяти для NPC"""
        # Создать каталог хранения памяти
        memory_dir = os.path.join(os.path.dirname(__file__), 'memory_data', npc_name)
        os.makedirs(memory_dir, exist_ok=True)

        # Система памяти конфигурации
        memory_config = MemoryConfig(
            storage_path=memory_dir,
            working_memory_capacity=10,  # Последние 10 разговоров
            working_memory_tokens=2000,  # До 2000 токенов
            max_capacity=100,  # До 100 долговременных воспоминаний
            importance_threshold=0.3,  # Сосредоточьтесь на более важных воспоминаниях во время извлечения и интеграции.
            decay_factor=0.95  # коэффициент затухания во времени
        )

        # Создать диспетчер памяти
        memory_manager = MemoryManager(
            config=memory_config,
            user_id=npc_name,  # Использовать имя NPC в качестве user_id
            enable_working=True,  # Включить рабочую память (краткосрочно)
            enable_episodic=True,  # Активировать эпизодическую память (долговременную)
            enable_semantic=False,  # Семантическая память не требуется
            enable_perceptual=False  # перцептивная память не требуется
        )

        print(f"  💾 Система памяти {npc_name} инициализирована (путь хранения: {memory_dir})")

        return memory_manager
    
    def chat(self, npc_name: str, message: str, player_id: str = "player") -> str:
        """Поговорите с назначенным NPC (поддерживает функцию памяти и систему благосклонности)"""
        if npc_name not in self.agents:
            return f"Ошибка: NPC «{npc_name}» не существует."

        agent = self.agents[npc_name]
        memory_manager = self.memories.get(npc_name)

        if agent is None:
            # Ответ в режиме моделирования
            role = NPC_ROLES[npc_name]
            return f"Привет! Я {npc_name}, {role['title']}. (В настоящее время в режиме симуляции настройте API_KEY, чтобы включить диалог AI)"

        try:
            # Запишите начало разговора ⭐ Используйте систему регистрации
            log_dialogue_start(npc_name, message)

            # ⭐ 1. Получите текущую благосклонность
            affinity_context = ""
            if self.relationship_manager:
                affinity = self.relationship_manager.get_affinity(npc_name, player_id)
                affinity_level = self.relationship_manager.get_affinity_level(affinity)
                affinity_modifier = self.relationship_manager.get_affinity_modifier(affinity)

                affinity_context = f"""【Текущие отношения】
Ваши отношения с игроком: {affinity_level} (предпочтительность: {affinity:.0f}/100)
【Стиль разговора】{affinity_modifier}

"""
                log_affinity(npc_name, affinity, affinity_level)

            # ⭐ 2. Вызовите соответствующие воспоминания.
            relevant_memories = []
            if memory_manager:
                relevant_memories = memory_manager.retrieve_memories(
                    query=message,
                    memory_types=["working", "episodic"],
                    limit=5,
                    min_importance=0.3  # Извлекайте только воспоминания с важностью >= 0,3.
                )
                log_memory_retrieval(npc_name, len(relevant_memories), relevant_memories)

            # ⭐ 3. Создайте расширенные слова-подсказки (включая контекст благоприятности и памяти)
            memory_context = self._build_memory_context(relevant_memories)

            enhanced_message = affinity_context
            if memory_context:
                enhanced_message += f"{memory_context}\n\n"
            enhanced_message += f"【Текущий разговор】\nИгрок: {сообщение}"

            # ⭐ 4. Позвоните агенту, чтобы получить ответ.
            log_generating_response()
            response = agent.run(enhanced_message)
            log_npc_response(npc_name, response)

            # ⭐ 5. Анализируйте и обновляйте информацию о благоприятности.
            log_analyzing_affinity()
            if self.relationship_manager:
                affinity_result = self.relationship_manager.analyze_and_update_affinity(
                    npc_name=npc_name,
                    player_message=message,
                    npc_response=response,
                    player_id=player_id
                )

                # Записывайте подробности изменений в благосклонности ⭐ Используйте систему журналов.
                log_affinity_change(affinity_result)
            else:
                affinity_result = {"changed": False, "affinity": 50.0}

            # ⭐ 6. Сохраните разговор в памяти (включая информацию о благосклонности)
            if memory_manager:
                self._save_conversation_to_memory(
                    memory_manager=memory_manager,
                    npc_name=npc_name,
                    player_message=message,
                    npc_response=response,
                    player_id=player_id,
                    affinity_info=affinity_result
                )
                log_memory_saved(npc_name)

            # Запишите окончание разговора. ⭐ Используйте систему регистрации.
            log_dialogue_end()

            return response

        except Exception as e:
            print(f"❌ Не удалось провести диалог с {npc_name}: {e}")
            import traceback
            traceback.print_exc()
            return f"Извините, я сейчас немного занят. Давай поговорим позже. (Ошибка: {str(e)})"
    
    def _build_memory_context(self, memories: List[MemoryItem]) -> str:
        """Создайте контекст памяти"""
        if not memories:
            return ""

        context_parts = ["[Память о предыдущих разговорах]"]
        for memory in memories:
            # Формат времени
            time_str = memory.timestamp.strftime("%H:%M")
            # Добавить содержимое памяти
            context_parts.append(f"[{time_str}] {memory.content}")

        context_parts.append("")  # Пустая строка отделена
        return "\n".join(context_parts)

    def _save_conversation_to_memory(
        self,
        memory_manager: MemoryManager,
        npc_name: str,
        player_message: str,
        npc_response: str,
        player_id: str,
        affinity_info: Optional[Dict] = None
    ):
        """Сохранение диалога в систему памяти (включая информацию о благосклонности)"""
        current_time = datetime.now()

        # Получить информацию о благосклонности
        affinity = affinity_info.get("new_affinity", affinity_info.get("affinity", 50.0)) if affinity_info else 50.0
        affinity_change = affinity_info.get("change_amount", 0) if affinity_info else 0
        sentiment = affinity_info.get("sentiment", "neutral") if affinity_info else "neutral"

        # Сохранять сообщения игрока
        memory_manager.add_memory(
            content=f"Игрок сказал: {player_message}",
            memory_type="working",  # Сначала сохраните в оперативной памяти
            importance=0.5,  # средняя важность
            metadata={
                "speaker": "player",
                "player_id": player_id,
                "session_id": player_id,
                "timestamp": current_time.isoformat(),
                "affinity": affinity,  # ⭐ Запишите благосклонность в это время
                "affinity_change": affinity_change,  # ⭐ Зафиксируйте изменения в благоприятности
                "sentiment": sentiment,  # ⭐ Записывайте эмоциональные тенденции
                "context": {
                    "interaction_type": "dialogue",
                    "npc_name": npc_name
                }
            }
        )

        # Сохранить ответ NPC
        memory_manager.add_memory(
            content=f"Я сказал: {npc_response}",
            memory_type="working",  # Сначала сохраните в оперативной памяти
            importance=0.6,  # немного более высокая важность
            metadata={
                "speaker": npc_name,
                "player_id": player_id,
                "session_id": player_id,
                "timestamp": current_time.isoformat(),
                "affinity": affinity,  # ⭐ Запишите благосклонность в это время
                "sentiment": sentiment,  # ⭐ Записывайте эмоциональные тенденции
                "context": {
                    "interaction_type": "dialogue",
                    "npc_name": npc_name
                }
            }
        )

        print(f"  💾 Разговор сохранен в памяти {npc_name}.")

    def get_npc_info(self, npc_name: str) -> Dict[str, str]:
        """Получить информацию о NPC"""
        if npc_name not in NPC_ROLES:
            return {}

        role = NPC_ROLES[npc_name]
        return {
            "name": npc_name,
            "title": role["title"],
            "location": role["location"],
            "activity": role["activity"],
            "available": self.agents.get(npc_name) is not None
        }
    
    def get_all_npcs(self) -> list:
        """Получить всю информацию о NPC"""
        return [self.get_npc_info(name) for name in NPC_ROLES.keys()]

    def get_npc_memories(self, npc_name: str, player_id: str = "player", limit: int = 10) -> List[Dict]:
        """Получить список памяти NPC (для отладки и отображения)"""
        if npc_name not in self.memories:
            return []

        memory_manager = self.memories[npc_name]
        if not memory_manager:
            return []

        try:
            # Восстановить все воспоминания
            memories = memory_manager.retrieve_memories(
                query="",  # Пустой запрос возвращает все воспоминания
                memory_types=["working", "episodic"],
                limit=limit
            )

            # Преобразовать в формат словаря
            memory_list = []
            for memory in memories:
                memory_list.append({
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.memory_type,
                    "importance": memory.importance,
                    "timestamp": memory.timestamp.isoformat(),
                    "metadata": memory.metadata
                })

            return memory_list

        except Exception as e:
            print(f"❌ Не удалось получить память {npc_name}: {e}.")
            return []

    def clear_npc_memory(self, npc_name: str, memory_type: Optional[str] = None):
        """Очистить память NPC (для тестирования)"""
        if npc_name not in self.memories:
            print(f"❌ NPC '{npc_name}' не существует.")
            return

        memory_manager = self.memories[npc_name]
        if not memory_manager:
            print(f"❌ У {npc_name} нет системы памяти.")
            return

        try:
            if memory_type:
                # Очистить память указанного типа
                memory_manager.clear_memory_type(memory_type)
                print(f"✅ Память {memory_type} у {npc_name} очищена.")
            else:
                # Очистить все воспоминания
                for mem_type in ["working", "episodic"]:
                    try:
                        memory_manager.clear_memory_type(mem_type)
                    except:
                        pass
                print(f"✅ Все воспоминания о {npc_name} удалены.")

        except Exception as e:
            print(f"❌ Не удалось очистить память {npc_name}: {e}.")

    def get_npc_affinity(self, npc_name: str, player_id: str = "player") -> Dict:
        """Получите информацию о благосклонности NPC к игроку.

        Аргументы:
            npc_name: имя NPC
            player_id: идентификатор игрока

        Возврат:
            Информационный словарь благоприятности
        """
        if not self.relationship_manager:
            return {
                "affinity": 50.0,
                "level": "привычный",
                "modifier": "Будьте вежливы и дружелюбны, общайтесь нормально и сохраняйте профессионализм."
            }

        affinity = self.relationship_manager.get_affinity(npc_name, player_id)
        level = self.relationship_manager.get_affinity_level(affinity)
        modifier = self.relationship_manager.get_affinity_modifier(affinity)

        return {
            "affinity": affinity,
            "level": level,
            "modifier": modifier
        }

    def get_all_affinities(self, player_id: str = "player") -> Dict[str, Dict]:
        """Получите информацию о благосклонности всех NPC.

        Аргументы:
            player_id: идентификатор игрока

        Возврат:
            Информация о благосклонности всех NPC
        """
        if not self.relationship_manager:
            return {}

        return self.relationship_manager.get_all_affinities(player_id)

    def set_npc_affinity(self, npc_name: str, affinity: float, player_id: str = "player"):
        """Установите благосклонность NPC к игроку (для тестирования)

        Аргументы:
            npc_name: имя NPC
            близость: значение благосклонности (0-100)
            player_id: идентификатор игрока
        """
        if not self.relationship_manager:
            print("❌ Система благосклонности не инициализирована")
            return

        self.relationship_manager.set_affinity(npc_name, affinity, player_id)
        level = self.relationship_manager.get_affinity_level(affinity)
        print(f"✅ Установлена ​​благосклонность {npc_name} к игроку: {affinity:.1f} ({level})")

# Глобальный синглтон
_npc_manager = None

def get_npc_manager() -> NPCAgentManager:
    """Получить синглтон менеджера NPC"""
    global _npc_manager
    if _npc_manager is None:
        _npc_manager = NPCAgentManager()
    return _npc_manager

