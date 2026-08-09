"""Менеджер статуса NPC — регулярные пакетные обновления разговоров с NPC."""

import asyncio
from datetime import datetime
from typing import Dict, Optional
from batch_generator import get_batch_generator

class NPCStateManager:
    """Менеджер статуса NPC
    
    Функция:
    1. Генерируйте разговоры с NPC в пакетном режиме через регулярные промежутки времени (сократите затраты на API).
    2. Кэшировать текущий статус NPC.
    3. Предоставьте интерфейс запроса статуса.
    """
    
    def __init__(self, update_interval: int = 30):
        """Инициализировать государственный менеджер
        
        Аргументы:
            update_interval: интервал обновления (в секундах), по умолчанию 30 секунд.
        """
        self.update_interval = update_interval
        self.batch_generator = get_batch_generator()
        
        # Текущий статус
        self.current_dialogues: Dict[str, str] = {}
        self.last_update: Optional[datetime] = None
        self.next_update_time: Optional[datetime] = None
        
        # Фоновые задачи
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
        
        print(f"📊 Инициализация менеджера статуса NPC завершена (интервал обновления: {update_interval} секунд)")
    
    async def start(self):
        """Запустить задачу фонового обновления"""
        if self._running:
            print("⚠️ Стат-менеджер уже запущен")
            return
        
        self._running = True
        print("🚀 Запустить автоматическое обновление статуса NPC...")
        
        # Выполните обновление сейчас
        await self._update_npc_states()
        
        # Запустить задачу запланированного обновления
        self._update_task = asyncio.create_task(self._auto_update_loop())
    
    async def stop(self):
        """Остановить задачи фонового обновления"""
        if not self._running:
            return
        
        self._running = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        print("🛑 Автоматическое обновление статуса NPC остановлено.")
    
    async def _auto_update_loop(self):
        """цикл автоматического обновления"""
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                await self._update_npc_states()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Не удалось выполнить автоматическое обновление: {e}")
                # Продолжайте работать без перерыва
    
    async def _update_npc_states(self):
        """Обновить статус NPC"""
        try:
            print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Начать пакетное обновление разговоров с NPC...")
            
            # Генерируйте разговоры в пакетном режиме
            new_dialogues = self.batch_generator.generate_batch_dialogues()
            
            # обновить статус
            self.current_dialogues = new_dialogues
            self.last_update = datetime.now()
            self.next_update_time = datetime.now()
            
            # Распечатать результаты обновления
            print("📝 Обновлены диалоги NPC:")
            for npc_name, dialogue in new_dialogues.items():
                print(f"   - {npc_name}: {dialogue}")
            
        except Exception as e:
            print(f"❌ Не удалось обновить статус NPC: {e}.")
    
    def get_current_state(self) -> Dict:
        """Получить текущий статус"""
        # Рассчитать обратный отсчет до следующего обновления
        if self.last_update:
            elapsed = (datetime.now() - self.last_update).total_seconds()
            next_update_in = max(0, int(self.update_interval - elapsed))
        else:
            next_update_in = self.update_interval
        
        return {
            "dialogues": self.current_dialogues,
            "last_update": self.last_update,
            "next_update_in": next_update_in
        }
    
    def get_npc_dialogue(self, npc_name: str) -> Optional[str]:
        """Получить текущий разговор указанного NPC"""
        return self.current_dialogues.get(npc_name)
    
    async def force_update(self):
        """Принудительное немедленное обновление"""
        print("⚡ Принудительное обновление статуса NPC...")
        await self._update_npc_states()

# Глобальный синглтон
_state_manager = None

def get_state_manager(update_interval: int = 30) -> NPCStateManager:
    """Получить синглтон менеджера состояний"""
    global _state_manager
    if _state_manager is None:
        _state_manager = NPCStateManager(update_interval)
    return _state_manager

