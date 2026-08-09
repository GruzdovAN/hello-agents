"""Система регистрации разговоров"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Создать каталог журналов
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Создать имя файла журнала (по дате)
today = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOGS_DIR / f"dialogue_{today}.log"

# Настроить формат журнала
LOG_FORMAT = "%(asctime)s - %(message)s"
DATE_FORMAT = "%H:%M:%S"

# Создать регистратор
dialogue_logger = logging.getLogger("dialogue")
dialogue_logger.setLevel(logging.INFO)

# Удалите существующие обработчики (во избежание дублирования)
dialogue_logger.handlers.clear()

# Создать обработчик файлов
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Создать обработчик консоли
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

# Добавить обработчики
dialogue_logger.addHandler(file_handler)
dialogue_logger.addHandler(console_handler)

# Запретить распространение журналов на корневой регистратор
dialogue_logger.propagate = False

def log_dialogue_start(npc_name: str, player_message: str):
    """Запись разговора начинается"""
    dialogue_logger.info("=" * 60)
    dialogue_logger.info(f"💬 Начинается разговор: {npc_name} <-> player")
    dialogue_logger.info("=" * 60)
    dialogue_logger.info(f"📝 Сообщение игрока: {player_message}")

def log_affinity(npc_name: str, affinity: float, level: str):
    """Записать текущую благосклонность"""
    dialogue_logger.info(f"💖 Текущая благосклонность: {affinity:.1f}/100 ({level})")

def log_memory_retrieval(npc_name: str, count: int, memories: list = None):
    """Запись восстановления памяти"""
    dialogue_logger.info(f"🧠 Получено связанных воспоминаний: {count}.")
    if memories:
        dialogue_logger.info("  📚Связанные воспоминания:")
        for i, mem in enumerate(memories[:3], 1):
            content = mem.content[:50] + "..." if len(mem.content) > 50 else mem.content
            dialogue_logger.info(f"    {i}. {content}")

def log_generating_response():
    """Запись генерирует ответ"""
    dialogue_logger.info("🤖 Генерируем ответ...")

def log_npc_response(npc_name: str, response: str):
    """Записывайте ответы NPC"""
    dialogue_logger.info(f"💬 {npc_name} ответил: {response}")

def log_analyzing_affinity():
    """Запись анализирует благоприятность"""
    dialogue_logger.info("📊Анализируем изменения в благоприятности...")

def log_affinity_change(affinity_result: dict):
    """Зафиксируйте изменения в благосклонности"""
    if affinity_result.get("changed"):
        change_symbol = "📈" if affinity_result["change_amount"] > 0 else "📉"
        dialogue_logger.info(
            f"{change_symbol} Изменение привязки: {affinity_result['old_affinity']:.1f} -> "
            f"{affinity_result['new_affinity']:.1f} ({affinity_result['change_amount']:+.1f})"
        )
        dialogue_logger.info(f"  Причина: {affinity_result['причина']}")
        dialogue_logger.info(f"  Сходство: {affinity_result['sentiment']}")
        
        if affinity_result['old_level'] != affinity_result['new_level']:
            dialogue_logger.info(
                f"  🎉 Изменение уровня отношений: {affinity_result['old_level']} -> {affinity_result['new_level']}"
            )
    else:
        dialogue_logger.info(f"  ➡️ Предпочтение не изменилось (текущее: {affinity_result.get('affinity', 50.0):.1f})")
        dialogue_logger.info(f"  Причина: {affinity_result.get('причина', 'Нет')}")

def log_memory_saved(npc_name: str):
    """запись в память сохранить"""
    dialogue_logger.info(f"  💾 Разговор сохранен в памяти {npc_name}.")

def log_dialogue_end():
    """Конец записанного разговора"""
    dialogue_logger.info("=" * 60)
    dialogue_logger.info("✅Разговор завершен\n")

def log_info(message: str):
    """Запишите общую информацию"""
    dialogue_logger.info(message)

def log_error(message: str):
    """Сообщение об ошибке журнала"""
    dialogue_logger.error(message)

# Местоположение файла журнала, записанное при запуске
print(f"\n📝 Файл журнала разговора: {LOG_FILE}")
print(f"📂 Каталог журналов: {LOGS_DIR}\n")

