"""Просматривайте журналы разговоров в режиме реального времени"""

import os
import time
from pathlib import Path
from datetime import datetime

# Каталог журналов
LOGS_DIR = Path(__file__).parent / "logs"
today = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOGS_DIR / f"dialogue_{today}.log"

def tail_log_file(filename, interval=1):
    """Просмотр файлов журналов в реальном времени (аналогично Tail -f)"""
    
    print("\n" + "="*60)
    print(f"📝 Просматривайте журналы разговоров в режиме реального времени")
    print(f"📂 Файл журнала: {имя файла}")
    print("="*60)
    print("\nНажмите Ctrl+C, чтобы остановить просмотр\n")
    
    # Если файл не существует, дождитесь создания
    while not filename.exists():
        print(f"⏳ Ожидание создания файла журнала: {filename}")
        time.sleep(interval)
    
    # открыть файл
    with open(filename, 'r', encoding='utf-8') as f:
        # Перейти в конец файла
        f.seek(0, 2)
        
        try:
            while True:
                line = f.readline()
                if line:
                    print(line, end='')
                else:
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n ✅ Прекратить просмотр журналов")

def view_full_log(filename):
    """Посмотреть полный журнал"""
    
    print("\n" + "="*60)
    print(f"📝 Посмотреть полный журнал разговоров")
    print(f"📂 Файл журнала: {имя файла}")
    print("="*60 + "\n")
    
    if not filename.exists():
        print(f"❌ Файл журнала не существует: {имя файла}.")
        return
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    
    print("\n" + "="*60)
    print("✅ Просмотр журнала завершен")
    print("="*60 + "\n")

def list_log_files():
    """Список всех файлов журналов"""
    
    print("\n" + "="*60)
    print(f"📂 Список файлов журнала")
    print(f"📁 Каталог: {LOGS_DIR}")
    print("="*60 + "\n")
    
    if not LOGS_DIR.exists():
        print("❌ Каталог журналов не существует.")
        return
    
    log_files = sorted(LOGS_DIR.glob("dialogue_*.log"), reverse=True)
    
    if not log_files:
        print("📭 Файлов журналов пока нет.")
        return
    
    for i, log_file in enumerate(log_files, 1):
        size = log_file.stat().st_size
        size_kb = size / 1024
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"{i}. {log_file.name}")
        print(f"   Размер: {size_kb:.2f} КБ.")
        print(f"   Время модификации: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "tail":
            # Просмотр в реальном времени
            tail_log_file(LOG_FILE)
        elif command == "view":
            # Посмотреть полный журнал
            view_full_log(LOG_FILE)
        elif command == "list":
            # Список всех журналов
            list_log_files()
        else:
            print(f"❌ Неизвестная команда: {команда}")
            print("\nИспользование:")
            print("  python view_logs.py Tail # Просмотр журналов в реальном времени")
            print("  python view_logs.py view # Просмотр полного журнала")
            print("  python view_logs.py list # Список всех файлов журналов")
    else:
        # Представление в реальном времени по умолчанию
        tail_log_file(LOG_FILE)

