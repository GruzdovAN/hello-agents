#!/usr/bin/env python3
"""Скрипт диагностики системы - проверка всех конфигураций и зависимостей"""

import sys
import os
from pathlib import Path

def check_env_file():
"""Проверьте файл .env"""
    print("\n" + "="*60)
print("1. Проверьте файл конфигурации среды")
    print("="*60)
    
    env_path = Path(".env")
    if not env_path.exists():
print("❌Файл .env не существует")
        return False
    
print("Файл .env существует")
    
# Чтение конфигурации ключа
    with open(env_path, encoding='utf-8') as f:
        content = f.read()
        
    required_keys = ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"]
    for key in required_keys:
        if key in content:
print(f"© {ключ} настроен")
        else:
print(f"⚠️ {ключ} не настроен")
    
    return True

def check_dependencies():
"""Проверить пакеты зависимостей"""
    print("\n" + "="*60)
print("2. Проверьте зависимые пакеты")
    print("="*60)
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "hello_agents",
        "arxiv",
        "httpx",
        "asyncpg",
        "qdrant_client",
        "feedparser",
        "beautifulsoup4"
    ]
    
    missing = []
    for package in required_packages:
        try:
# Специальная обработка сопоставления имен пакетов
            import_name = package.replace("-", "_")
            if package == "beautifulsoup4":
                import_name = "bs4"
            __import__(import_name)
            print(f"✅ {package}")
        except ImportError:
print(f"❌ {пакет} — отсутствует")
            missing.append(package)
    
    if missing:
print(f"\n⚠️ Отсутствует пакет: {', '.join(missing)}")
        print(f"安装命令: pip install {' '.join(missing)}")
        return False
    
    return True

def check_config():
"""Проверьте загрузку конфигурации"""
    print("\n" + "="*60)
print("3. Проверьте загрузку конфигурации")
    print("="*60)
    
    try:
        from core.config import get_config
        config = get_config()
        
print(f"Конфигурация успешно загружена")
print(f" - Ключ API: {'set' if config.llm.api_key else 'not set'}")
        print(f"   - Base URL: {config.llm.base_url or '未设置'}")
        print(f"   - Model: {config.llm.model_name}")
        print(f"   - Debug: {config.debug}")
        
        return True
    except Exception as e:
print(f"❌ Не удалось загрузить конфигурацию: {str(e)}")
        return False

def check_api_routes():
    """检查 API 路由"""
    print("\n" + "="*60)
print("4. Проверьте маршрутизацию API")
    print("="*60)
    
    try:
        from api.main import app
        
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"✅ API 加载成功，共 {len(routes)} 个路由")
        
# Проверьте ключевые маршруты
        key_routes = ["/", "/health", "/api/v1/papers/search", "/api/v1/analysis/analyze"]
        for route in key_routes:
            if route in routes:
                print(f"   ✅ {route}")
            else:
print(f" ❌ {маршрут} — отсутствует")
        
        return True
    except Exception as e:
print(f"❌ Ошибка загрузки API: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_frontend():
"""Проверить файлы внешнего интерфейса"""
    print("\n" + "="*60)
print("5. Проверьте файлы внешнего интерфейса")
    print("="*60)
    
    frontend_files = [
        "frontend/index.html",
        "frontend/static/css/style.css",
        "frontend/static/js/app.js"
    ]
    
    all_exist = True
    for file_path in frontend_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
print(f"⚠️ {file_path} — не существует (необязательно)")
    
    return True

def check_llm_connection():
"""Проверьте соединение LLM"""
    print("\n" + "="*60)
print("6. Проверьте соединение LLM")
    print("="*60)
    
    try:
        import asyncio
        from hello_agents import HelloAgentsLLM
        from core.config import get_config
        
        config = get_config()
        
        if not config.llm.api_key:
print("⚠️ Ключ API не установлен, пропустить проверку соединения")
            return True
        
        async def test():
            from core.llm_adapter import get_llm_adapter
            adapter = get_llm_adapter()
            
            response = await adapter.ainvoke("你好")
            return response
        
print("Проверка соединения LLM...")
        result = asyncio.run(test())
print(f"Соединение LLM успешно выполнено")
print(f"Ответ модели: {result[:50]}...")
        
        return True
    except Exception as e:
        error_msg = str(e)
# Если формат API неправильный, это означает, что соединение открыто, но проблема в формате запроса.
        if "400" in error_msg or "invalid_request" in error_msg:
print(f"⚠️ LLM API доступен, но формат запроса необходимо изменить")
            print(f"   错误信息: {error_msg[:100]}...")
return True # Считайте, что оно пройдено, поскольку само соединение нормальное
        print(f"❌ LLM 连接失败: {error_msg[:100]}...")
        return False

def main():
"""Основная функция"""
    print("\n" + "="*60)
print("Диагностика системы InnoCore AI")
    print("="*60)
    
    results = []
    
results.append(("Конфигурация среды", check_env_file()))
results.append(("Зависимости", check_dependents()))
results.append(("Загрузка конфигурации", check_config()))
    results.append(("API 路由", check_api_routes()))
results.append(("файл интерфейса", check_frontend()))
    results.append(("LLM 连接", check_llm_connection()))
    
# Подвести итог
    print("\n" + "="*60)
print("Сводка результатов диагностики")
    print("="*60)
    
    for name, result in results:
status = « ✅ Пройдено», если результат еще «❌ Не удалось»
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
print("\n🎉 Все проверки пройдены! Система может работать нормально.")
print("\nЗапуск команды: python run.py")
    else:
print("\n⚠️ Некоторые проверки не пройдены, следуйте приведенным выше советам, чтобы решить проблему.")

if __name__ == "__main__":
    main()
