"""Система управления благосклонностью NPC"""

import sys
import os

# Добавить HelloAgents в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))

from hello_agents import SimpleAgent, HelloAgentsLLM
from typing import Dict, Optional, Tuple
import json
import re

class RelationshipManager:
    """Менеджер по благосклонности NPC
    
    Функция:
    - Управляйте благосклонностью NPC и игроков (0-100)
    - Используйте LLM для анализа настроений в разговоре.
    - Автоматически обновлять благосклонность
    - Обеспечить уровни благосклонности и модификаторы
    """
    
    def __init__(self, llm: HelloAgentsLLM):
        """Инициализировать менеджер предпочтений
        
        Аргументы:
            llm: экземпляр HelloAgentsLLM
        """
        self.llm = llm
        
        # Сохраняйте расположение между каждым NPC и игроком.
        # Формат: {npc_name: {player_id: affinity_score}}
        self.affinity_scores: Dict[str, Dict[str, float]] = {}
        
        # Создайте агента анализа благоприятности
        self.analyzer_agent = SimpleAgent(
            name="AffinityAnalyzer",
            llm=llm,
            system_prompt=self._create_analyzer_prompt()
        )
        
        print("💖 Запущена система управления благосклонностью")
    
    def _create_analyzer_prompt(self) -> str:
        """Создание слов системной подсказки для агента анализа настроений"""
        return """Вы эксперт по эмоциональному анализу, ответственный за анализ эмоциональных тенденций в разговорах и определение того, следует ли изменить благосклонность NPC к игроку.

【Задание】
Проанализируйте разговор между игроком и NPC, чтобы определить, следует ли изменить благосклонность и степень изменения.

[Измерение анализа]
1. **Отношение игроков**: Дружелюбное/Нейтральное/Недружественное.
2. **Содержание разговора**: Положительное/Нейтральное/Отрицательное.
3. **Качество взаимодействия**: глубокое/посредственное/поверхностное.
4. **Эмоциональная тенденция**: похвала/критика/нейтральность.

[Правила изменения благоприятности]
- Хвалить, благодарить, просить совета: от +3 до +8.
- Дружеские приветствия и нормальное общение: от +1 до +3
- Общий светский разговор, нейтральные темы: 0
- Критика, сомнения, нетерпение: от -3 до -8.
- Оскорбление, нападение, злой умысел: от -8 до -15.

[Формат вывода] (Строго придерживайтесь формата JSON, не добавляйте другой текст)
{
    «should_change»: правда/ложь,
    «change_amount»: целое число от -15 до +10,
    "reason": "Кратко опишите причину (до 10 слов)",
    «настроение»: «положительное/нейтральное/отрицательное»
}

【Пример 1】
Игрок: «Привет, приятно познакомиться!»
NPC: «Привет! Тоже приятно с вами познакомиться».
Вывод: {"should_change": true, "change_amount": 5, "причина": "дружеский привет", "настроения": "положительный"}

【Пример 2】
Игрок: «У тебя такой уродливый дизайн!»
NPC: "Извините, я исправлюсь..."
Вывод: {"should_change": true, "change_amount": -8, "причина": "критическая работа", "настроения": "негативный"}

【Пример 3】
Игрок: «Погода сегодня хорошая»
NPC: «Да, довольно хорошо».
Вывод: {"should_change": false, "change_amount": 0, "причина": "нейтрально", "настроения": "нейтрально"}

【Пример 4】
Игрок: «Ваш код потрясающий!»
NPC: «Спасибо! Недавно я изучал новые технологии».
Вывод: {"should_change": true, "change_amount": 8, "причина": "Похвала за работу", "настроения": "положительно"}

【Пример 5】
Игрок: «Можете ли вы меня научить?»
NPC: «Конечно! Буду рад поделиться».
Вывод: {"should_change": true, "change_amount": 6, "причина": "спрашивать совета и учиться", "sentiment": "положительно"}

【Важно】
- Выводите только JSON, не добавляйте пояснений или другого текста.
- Change_amount должно быть целым числом
- причина должна быть короткой (до 10 слов)
- Настроение должно быть одним из положительных/нейтральных/отрицательных.
"""
    
    def get_affinity(self, npc_name: str, player_id: str = "player") -> float:
        """Получить благосклонность (0-100)
        
        Аргументы:
            npc_name: имя NPC
            player_id: идентификатор игрока
            
        Возврат:
            Значение благоприятности (0-100)
        """
        if npc_name not in self.affinity_scores:
            self.affinity_scores[npc_name] = {}
        
        if player_id not in self.affinity_scores[npc_name]:
            self.affinity_scores[npc_name][player_id] = 50.0  # Начальная благосклонность равна 50.
        
        return self.affinity_scores[npc_name][player_id]
    
    def set_affinity(self, npc_name: str, affinity: float, player_id: str = "player"):
        """Установить благосклонность
        
        Аргументы:
            npc_name: имя NPC
            близость: значение благосклонности (0-100)
            player_id: идентификатор игрока
        """
        if npc_name not in self.affinity_scores:
            self.affinity_scores[npc_name] = {}
        
        # Ограничение в диапазоне 0-100
        affinity = max(0.0, min(100.0, affinity))
        self.affinity_scores[npc_name][player_id] = affinity
    
    def analyze_and_update_affinity(
        self,
        npc_name: str,
        player_message: str,
        npc_response: str,
        player_id: str = "player"
    ) -> Dict:
        """Анализируйте разговоры и обновляйте информацию о благосклонности
        
        Аргументы:
            npc_name: имя NPC
            player_message: сообщение игрока
            npc_response: ответ NPC
            player_id: идентификатор игрока
            
        Возврат:
            Словарь результатов анализа
        """
        # Подсказки для анализа сборки
        prompt = f"""Проанализируйте, пожалуйста, следующий разговор:

Игрок: {player_message}
{npc_name}: {npc_response}

Пожалуйста, оцените, следует ли изменить благосклонность, и укажите сумму изменения.
"""
        
        try:
            # Позвоните агенту по анализу
            response = self.analyzer_agent.run(prompt)
            
            # Разобрать ответ JSON
            analysis = self._parse_analysis(response)
            
            if analysis["should_change"]:
                # Обновить предпочтения
                current_affinity = self.get_affinity(npc_name, player_id)
                new_affinity = current_affinity + analysis["change_amount"]
                new_affinity = max(0.0, min(100.0, new_affinity))  # Ограничение до 0-100

                self.set_affinity(npc_name, new_affinity, player_id)

                # Получить уровень благосклонности
                old_level = self.get_affinity_level(current_affinity)
                new_level = self.get_affinity_level(new_affinity)

                # Примечание. Журнал печати был перенесен в агенты.py, чтобы избежать повторного вывода.

                return {
                    "changed": True,
                    "old_affinity": current_affinity,
                    "new_affinity": new_affinity,
                    "change_amount": analysis["change_amount"],
                    "reason": analysis["reason"],
                    "sentiment": analysis.get("sentiment", "neutral"),
                    "old_level": old_level,
                    "new_level": new_level
                }
            else:
                return {
                    "changed": False,
                    "affinity": self.get_affinity(npc_name, player_id),
                    "reason": analysis["reason"],
                    "sentiment": analysis.get("sentiment", "neutral")
                }
        
        except Exception as e:
            print(f"❌ Анализ благоприятности не удался: {e}")
            import traceback
            traceback.print_exc()
            return {
                "changed": False,
                "affinity": self.get_affinity(npc_name, player_id),
                "reason": "Анализ не удался",
                "sentiment": "neutral"
            }
    
    def _parse_analysis(self, response: str) -> Dict:
        """Анализ результатов анализа
        
        Аргументы:
            ответ: ответ LLM
            
        Возврат:
            анализируемый словарь
        """
        try:
            # Попробуйте проанализировать JSON напрямую
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            # Попробуйте извлечь часть JSON
            # Найти первый { и последний }
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                try:
                    analysis = json.loads(json_str)
                    return analysis
                except json.JSONDecodeError:
                    pass
            
            # Попробуйте использовать регулярное выражение для извлечения
            # Соответствие «should_change»: true/false
            should_change_match = re.search(r'"should_change"\s*:\s*(true|false)', response, re.IGNORECASE)
            change_amount_match = re.search(r'"change_amount"\s*:\s*(-?\d+)', response)
            reason_match = re.search(r'"reason"\s*:\s*"([^"]+)"', response)
            sentiment_match = re.search(r'"sentiment"\s*:\s*"([^"]+)"', response)
            
            if should_change_match and change_amount_match:
                return {
                    "should_change": should_change_match.group(1).lower() == "true",
                    "change_amount": int(change_amount_match.group(1)),
                    "reason": reason_match.group(1) if reason_match else "неизвестный",
                    "sentiment": sentiment_match.group(1) if sentiment_match else "neutral"
                }
            
            # Анализ завершается неудачей и возвращает значение по умолчанию.
            print(f"⚠️ Не удалось выполнить синтаксический анализ JSON, используйте значение по умолчанию. Исходный ответ: {response[:100]}...")
            return {
                "should_change": False,
                "change_amount": 0,
                "reason": "Не удалось выполнить синтаксический анализ",
                "sentiment": "neutral"
            }
    
    def get_affinity_level(self, affinity: float) -> str:
        """Получить уровень благосклонности
        
        Аргументы:
            близость: значение благосклонности (0-100)
            
        Возврат:
            Название уровня предпочтительности
        """
        if affinity >= 80:
            return "лучший друг"
        elif affinity >= 60:
            return "закрывать"
        elif affinity >= 40:
            return "дружелюбно"
        elif affinity >= 20:
            return "привычный"
        else:
            return "странность"
    
    def get_affinity_modifier(self, affinity: float) -> str:
        """Получить модификаторы благосклонности (используются для настройки стиля разговора)
        
        Аргументы:
            близость: значение благосклонности (0-100)
            
        Возврат:
            модификатор разговорного стиля
        """
        if affinity >= 80:
            return "Очень теплый и дружелюбный, доступный, как старый друг, готовый поделиться личными темами."
        elif affinity >= 60:
            return "Дружелюбные и полные энтузиазма, желающие больше общаться и активно заботящиеся друг о друге."
        elif affinity >= 40:
            return "Будьте вежливы и дружелюбны, общайтесь нормально и сохраняйте профессионализм."
        elif affinity >= 20:
            return "Вежливый, но немного заржавевший, отвечайте кратко."
        else:
            return "Холодный и отстраненный, не желающий много говорить, дающий короткие ответы."
    
    def get_all_affinities(self, player_id: str = "player") -> Dict[str, Dict]:
        """Получите информацию о благосклонности всех NPC.
        
        Аргументы:
            player_id: идентификатор игрока
            
        Возврат:
            Информация о благосклонности всех NPC
        """
        result = {}
        for npc_name in self.affinity_scores:
            affinity = self.get_affinity(npc_name, player_id)
            result[npc_name] = {
                "affinity": affinity,
                "level": self.get_affinity_level(affinity),
                "modifier": self.get_affinity_modifier(affinity)
            }
        return result

