"""Пакетный генератор диалогов NPC"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Optional

# Добавить HelloAgents в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'HelloAgents'))

from hello_agents import HelloAgentsLLM
from agents import NPC_ROLES

class NPCBatchGenerator:
    """Генератор пакетной генерации диалогов NPC
    
    Основная идея: один вызов LLM генерирует все диалоги NPC, сокращая затраты на API и задержки.
    """
    
    def __init__(self):
        """Инициализировать пакетный генератор"""
        print("🎨 Инициализация генератора пакетных разговоров...")
        
        try:
            self.llm = HelloAgentsLLM()
            self.enabled = True
            print("✅ Пакетный генератор успешно инициализирован")
        except Exception as e:
            print(f"❌ Ошибка инициализации пакетного генератора: {e}")
            print("⚠️ Будет использоваться режим разговора по умолчанию.")
            self.llm = None
            self.enabled = False
        
        self.npc_configs = NPC_ROLES
        
        # Библиотека диалогов по умолчанию (используется, когда LLM недоступна)
        self.preset_dialogues = {
            "morning": {
                "Чжан Сан": "Доброе утро! Сегодня мы продолжим оптимизировать производительность этой мультиагентной системы.",
                "Джон Доу": "Начался новый день. Давайте разберемся с расписанием сегодняшних встреч.",
                "Ван Ву": "Утро! Давайте выпьем чашечку кофе, чтобы освежиться, а затем приступим к разработке нового интерфейса."
            },
            "noon": {
                "Чжан Сан": "После написания кода все утро я наконец исправил ошибку!",
                "Джон Доу": "Утреннее совещание по рассмотрению требований прошло гладко и продолжится во второй половине дня.",
                "Ван Ву": "Эта цветовая схема выглядит хорошо, давайте подправим детали."
            },
            "afternoon": {
                "Чжан Сан": "Я продолжу писать код во второй половине дня. Этот алгоритм еще нуждается в оптимизации.",
                "Джон Доу": "Мы готовимся к совещанию по планированию продукта на следующей неделе, и документ с требованиями почти завершен.",
                "Ван Ву": "Эскиз проекта в основном завершен и позже будет отправлен всем на рассмотрение."
            },
            "evening": {
                "Чжан Сан": "Сегодняшняя отправка кода завершена и продолжится завтра!",
                "Джон Доу": "Сегодняшняя работа почти закончена, давайте разберемся со списком завтрашних дел.",
                "Ван Ву": "Работы по проектированию подошли к концу, оптимизация продолжится завтра."
            }
        }
    
    def generate_batch_dialogues(self, context: Optional[str] = None) -> Dict[str, str]:
        """Пакетная генерация диалогов для всех NPC
        
        Аргументы:
            контекст: контекст сцены (например, «утреннее рабочее время», «обеденное время» и т. д.)
        
        Возврат:
            Dict[str, str]: Сопоставление имени NPC с содержимым диалога.
        """
        if not self.enabled or self.llm is None:
            # Использовать диалоги по умолчанию
            return self._get_preset_dialogues()
        
        try:
            # Создание подсказок для пакетной генерации
            prompt = self._build_batch_prompt(context)

            # Один звонок LLM генерирует все разговоры
            # Используйте метод вызова вместо метода чата
            response = self.llm.invoke([
                {"role": "system", "content": "Вы — игровой генератор диалогов NPC, умеющий создавать естественные и реалистичные офисные диалоги."},
                {"role": "user", "content": prompt}
            ])

            # Разобрать ответ JSON
            dialogues = self._parse_response(response)

            if dialogues:
                print(f"✅ Пакетная генерация прошла успешно: {len(dialogues)} диалоги NPC")
                return dialogues
            else:
                print("⚠️ Не удалось выполнить синтаксический анализ, используйте диалог по умолчанию.")
                return self._get_preset_dialogues()

        except Exception as e:
            print(f"❌ Не удалось создать пакет: {e}")
            return self._get_preset_dialogues()
    
    def _build_batch_prompt(self, context: Optional[str] = None) -> str:
        """Создание подсказок для пакетной генерации"""
        # Автоматически определять сцены на основе времени
        if context is None:
            context = self._get_current_context()
        
        # Описание сборки NPC
        npc_descriptions = []
        for name, cfg in self.npc_configs.items():
            desc = f"- {name}({cfg['title']}): в {cfg['location']}{cfg['activity']}, личность {cfg['personality']}"
            npc_descriptions.append(desc)
        
        npc_desc_text = "\n".join(npc_descriptions)
        
        prompt = f"""Пожалуйста, создайте текущие описания диалогов или поведения для трех NPC в офисе Datawhale.

【Сценарий】{контекст}

【Информация о NPC】
{npc_desc_text}

[Требования к генерации]
1. Каждый NPC генерирует 1 предложение (20-40 слов).
2. Содержание должно соответствовать сеттингу персонажа, текущей деятельности и атмосфере сцены.
3. Это может быть разговор с самим собой, описание рабочего статуса или просто размышление.
4. Будьте естественными и искренними, как настоящие коллеги по офису.
5. Может отражать некоторые личные характеристики и эмоции.
6. **Должен быть возвращен строго в формате JSON**

[Формат вывода] (строго соблюдать)
{{"Чжан Сан": "...", "Ли Си": "...", "Ван Ву": "..."}}

[Пример вывода]
{{"Чжан Сан": "Эта ошибка настолько серьезна, я отлаживал ее два часа...", "Ли Си": "Ну, приоритет этой функции необходимо переоценить.", "Ван Ву": "Латте-арт в этой чашке кофе действительно хорош, пришло вдохновение!"}}

Пожалуйста, сгенерируйте (возвратите только JSON, без другого контента):
"""
        return prompt
    
    def _parse_response(self, response: str) -> Optional[Dict[str, str]]:
        """Разобрать ответ LLM"""
        try:
            # Попробуйте проанализировать JSON напрямую
            dialogues = json.loads(response)
            
            # Проверьте формат
            if isinstance(dialogues, dict) and all(name in dialogues for name in self.npc_configs.keys()):
                return dialogues
            else:
                print(f"⚠️ Неправильный формат JSON: {диалоги}.")
                return None
                
        except json.JSONDecodeError:
            # Попробуйте извлечь часть JSON
            try:
                # Найти первый {и последний}
                start = response.find('{')
                end = response.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = response[start:end]
                    dialogues = json.loads(json_str)
                    
                    if isinstance(dialogues, dict):
                        return dialogues
            except:
                pass
            
            print(f"⚠️ Невозможно разобрать ответ: {response[:100]}...")
            return None
    
    def _get_current_context(self) -> str:
        """Вывод контекста сцены на основе текущего времени"""
        hour = datetime.now().hour
        
        if 6 <= hour < 9:
            return "Ранним утром все один за другим приходят в офис, готовые начать новый день."
        elif 9 <= hour < 12:
            return "В утреннее рабочее время все сосредоточены на работе, а атмосфера в офисе сосредоточена и занята."
        elif 12 <= hour < 14:
            return "Во время обеда все расслабляются, болтают или смотрят на свои мобильные телефоны."
        elif 14 <= hour < 17:
            return "В дневное рабочее время я продолжаю продвигать проект, и иногда мне нужна чашка кофе, чтобы освежиться."
        elif 17 <= hour < 19:
            return "Вечером приготовьтесь подвести итоги сегодняшней работы и разобраться с планами на завтра."
        else:
            return "Ночью в офисе становится тихо, и иногда люди все еще работают сверхурочно."
    
    def _get_preset_dialogues(self) -> Dict[str, str]:
        """Получите заранее заданный разговор (в зависимости от времени)"""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 14:
            period = "noon"
        elif 14 <= hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        
        return self.preset_dialogues.get(period, self.preset_dialogues["morning"])

# Глобальный синглтон
_batch_generator = None

def get_batch_generator() -> NPCBatchGenerator:
    """Получить синглтон пакетного генератора"""
    global _batch_generator
    if _batch_generator is None:
        _batch_generator = NPCBatchGenerator()
    return _batch_generator

