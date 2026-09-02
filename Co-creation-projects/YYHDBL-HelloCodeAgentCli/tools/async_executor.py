"""Асинхронный исполнитель инструментов — поддержка параллельного выполнения HelloAgents"""

import asyncio
import concurrent.futures
from typing import Dict, Any, List
from .registry import ToolRegistry


class AsyncToolExecutor:
    """Асинхронный исполнитель инструментов"""

    def __init__(self, registry: ToolRegistry, max_workers: int = 4):
        self.registry = registry
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def execute_tool_async(self, tool_name: str, input_data: str) -> str:
        """Асинхронно выполняет один инструмент"""
        loop = asyncio.get_event_loop()
        
        def _execute():
            return self.registry.execute_tool(tool_name, input_data)
        
        try:
            result = await loop.run_in_executor(self.executor, _execute)
            return result
        except Exception as e:
            return f"❌ Асинхронное выполнение инструмента '{tool_name}' не удалось: {e}"

    async def execute_tools_parallel(self, tasks: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Параллельно выполняет несколько инструментов
        
        Args:
            tasks: список задач с tool_name и input_data
            
        Returns:
            Список результатов с информацией о задаче
        """
        print(f"🚀 Параллельный запуск {len(tasks)} задач инструментов")
        
        async_tasks = []
        for i, task in enumerate(tasks):
            tool_name = task.get("tool_name")
            input_data = task.get("input_data", "")
            
            if not tool_name:
                continue
                
            print(f"📝 Создана задача {i+1}: {tool_name}")
            async_task = self.execute_tool_async(tool_name, input_data)
            async_tasks.append((i, task, async_task))
        
        results = []
        for i, task, async_task in async_tasks:
            try:
                result = await async_task
                results.append({
                    "task_id": i,
                    "tool_name": task["tool_name"],
                    "input_data": task["input_data"],
                    "result": result,
                    "status": "success"
                })
                print(f"✅ Задача {i+1} завершена: {task['tool_name']}")
            except Exception as e:
                results.append({
                    "task_id": i,
                    "tool_name": task["tool_name"],
                    "input_data": task["input_data"],
                    "result": str(e),
                    "status": "error"
                })
                print(f"❌ Задача {i+1} не удалась: {task['tool_name']} - {e}")
        
        print(f"🎉 Параллельное выполнение завершено, успешно: {sum(1 for r in results if r['status'] == 'success')}/{len(results)}")
        return results

    async def execute_tools_batch(self, tool_name: str, input_list: List[str]) -> List[Dict[str, Any]]:
        """
        Пакетно выполняет один и тот же инструмент
        
        Args:
            tool_name: имя инструмента
            input_list: список входных данных
            
        Returns:
            Список результатов
        """
        tasks = [
            {"tool_name": tool_name, "input_data": input_data}
            for input_data in input_list
        ]
        return await self.execute_tools_parallel(tasks)

    def close(self):
        """Закрывает исполнитель"""
        self.executor.shutdown(wait=True)
        print("🔒 Асинхронный исполнитель инструментов закрыт")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


async def run_parallel_tools(registry: ToolRegistry, tasks: List[Dict[str, str]], max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    Удобная функция: параллельное выполнение нескольких инструментов
    
    Args:
        registry: реестр инструментов
        tasks: список задач
        max_workers: максимум рабочих потоков
        
    Returns:
        Список результатов
    """
    async with AsyncToolExecutor(registry, max_workers) as executor:
        return await executor.execute_tools_parallel(tasks)


async def run_batch_tool(registry: ToolRegistry, tool_name: str, input_list: List[str], max_workers: int = 4) -> List[Dict[str, Any]]:
    """
    Удобная функция: пакетное выполнение одного инструмента
    
    Args:
        registry: реестр инструментов
        tool_name: имя инструмента
        input_list: список входных данных
        max_workers: максимум рабочих потоков
        
    Returns:
        Список результатов
    """
    async with AsyncToolExecutor(registry, max_workers) as executor:
        return await executor.execute_tools_batch(tool_name, input_list)


def run_parallel_tools_sync(registry: ToolRegistry, tasks: List[Dict[str, str]], max_workers: int = 4) -> List[Dict[str, Any]]:
    """Синхронная обёртка параллельного выполнения инструментов"""
    return asyncio.run(run_parallel_tools(registry, tasks, max_workers))


def run_batch_tool_sync(registry: ToolRegistry, tool_name: str, input_list: List[str], max_workers: int = 4) -> List[Dict[str, Any]]:
    """Синхронная обёртка пакетного выполнения инструмента"""
    return asyncio.run(run_batch_tool(registry, tool_name, input_list, max_workers))


async def demo_parallel_execution():
    """Демонстрация параллельного выполнения"""
    from .registry import ToolRegistry
    
    registry = ToolRegistry()
    
    tasks = [
        {"tool_name": "my_calculator", "input_data": "2 + 2"},
        {"tool_name": "my_calculator", "input_data": "3 * 4"},
        {"tool_name": "my_calculator", "input_data": "sqrt(16)"},
        {"tool_name": "my_calculator", "input_data": "10 / 2"},
    ]
    
    results = await run_parallel_tools(registry, tasks)
    
    print("\n📊 Результаты параллельного выполнения:")
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['tool_name']}({result['input_data']}) = {result['result']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(demo_parallel_execution())
