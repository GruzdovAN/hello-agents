"""Менеджер цепочек инструментов — последовательный вызов HelloAgents"""

from typing import List, Dict, Any, Optional
from .registry import ToolRegistry


class ToolChain:
    """Цепочка инструментов — последовательное выполнение"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.steps: List[Dict[str, Any]] = []

    def add_step(self, tool_name: str, input_template: str, output_key: str = None):
        """
        Добавляет шаг выполнения инструмента
        
        Args:
            tool_name: имя инструмента
            input_template: шаблон ввода с подстановкой переменных, например "{input}" или "{search_result}"
            output_key: ключ результата для последующих шагов
        """
        step = {
            "tool_name": tool_name,
            "input_template": input_template,
            "output_key": output_key or f"step_{len(self.steps)}_result"
        }
        self.steps.append(step)
        print(f"✅ В цепочку '{self.name}' добавлен шаг: {tool_name}")

    def execute(self, registry: ToolRegistry, input_data: str, context: Dict[str, Any] = None) -> str:
        """
        Выполняет цепочку инструментов
        
        Args:
            registry: реестр инструментов
            input_data: начальные входные данные
            context: контекст выполнения для подстановки переменных
            
        Returns:
            Итоговый результат
        """
        if not self.steps:
            return "❌ Цепочка пуста, выполнение невозможно"

        print(f"🚀 Запуск цепочки инструментов: {self.name}")
        
        if context is None:
            context = {}
        context["input"] = input_data
        
        final_result = input_data
        
        for i, step in enumerate(self.steps):
            tool_name = step["tool_name"]
            input_template = step["input_template"]
            output_key = step["output_key"]
            
            print(f"📝 Шаг {i+1}/{len(self.steps)}: {tool_name}")
            
            try:
                actual_input = input_template.format(**context)
            except KeyError as e:
                return f"❌ Ошибка подстановки переменных в шаблон: {e}"
            
            try:
                result = registry.execute_tool(tool_name, actual_input)
                context[output_key] = result
                final_result = result
                print(f"✅ Шаг {i+1} завершён")
            except Exception as e:
                return f"❌ Инструмент '{tool_name}' завершился с ошибкой: {e}"
        
        print(f"🎉 Цепочка '{self.name}' выполнена")
        return final_result


class ToolChainManager:
    """Менеджер цепочек инструментов"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.chains: Dict[str, ToolChain] = {}

    def register_chain(self, chain: ToolChain):
        """Регистрирует цепочку инструментов"""
        self.chains[chain.name] = chain
        print(f"✅ Цепочка '{chain.name}' зарегистрирована")

    def execute_chain(self, chain_name: str, input_data: str, context: Dict[str, Any] = None) -> str:
        """Выполняет указанную цепочку"""
        if chain_name not in self.chains:
            return f"❌ Цепочка '{chain_name}' не существует"

        chain = self.chains[chain_name]
        return chain.execute(self.registry, input_data, context)

    def list_chains(self) -> List[str]:
        """Список зарегистрированных цепочек"""
        return list(self.chains.keys())

    def get_chain_info(self, chain_name: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о цепочке"""
        if chain_name not in self.chains:
            return None
        
        chain = self.chains[chain_name]
        return {
            "name": chain.name,
            "description": chain.description,
            "steps": len(chain.steps),
            "step_details": [
                {
                    "tool_name": step["tool_name"],
                    "input_template": step["input_template"],
                    "output_key": step["output_key"]
                }
                for step in chain.steps
            ]
        }


def create_research_chain() -> ToolChain:
    """Создаёт исследовательскую цепочку: поиск -> вычисление -> итог"""
    chain = ToolChain(
        name="research_and_calculate",
        description="Поиск информации и связанные вычисления"
    )

    chain.add_step(
        tool_name="search",
        input_template="{input}",
        output_key="search_result"
    )

    chain.add_step(
        tool_name="my_calculator",
        input_template="2 + 2",
        output_key="calc_result"
    )

    return chain


def create_simple_chain() -> ToolChain:
    """Простая демонстрационная цепочка"""
    chain = ToolChain(
        name="simple_demo",
        description="Простая демонстрация цепочки инструментов"
    )

    chain.add_step(
        tool_name="my_calculator",
        input_template="{input}",
        output_key="result"
    )

    return chain
