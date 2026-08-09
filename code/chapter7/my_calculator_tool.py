# my_calculator_tool.py
import ast
import operator
import math
from hello_agents import ToolRegistry

def my_calculate(expression: str) -> str:
    """Простые функции математических вычислений"""
    if not expression.strip():
        return "Выражение расчета не может быть пустым."

    # Поддерживаемые основные операции
    operators = {
        ast.Add: operator.add,      # +
        ast.Sub: operator.sub,      # -
        ast.Mult: operator.mul,     # *
        ast.Div: operator.truediv,  # /
    }

    # Поддерживаемые базовые функции
    functions = {
        'sqrt': math.sqrt,
        'pi': math.pi,
    }

    try:
        node = ast.parse(expression, mode='eval')
        result = _eval_node(node.body, operators, functions)
        return str(result)
    except:
        return "Расчет не выполнен, проверьте формат выражения."

def _eval_node(node, operators, functions):
    """Упрощенная оценка выражения"""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, operators, functions)
        right = _eval_node(node.right, operators, functions)
        op = operators.get(type(node.op))
        return op(left, right)
    elif isinstance(node, ast.Call):
        func_name = node.func.id
        if func_name in functions:
            args = [_eval_node(arg, operators, functions) for arg in node.args]
            return functions[func_name](*args)
    elif isinstance(node, ast.Name):
        if node.id in functions:
            return functions[node.id]

def create_calculator_registry():
    """Создайте реестр инструментов, содержащий калькулятор."""
    registry = ToolRegistry()

    # Зарегистрируйте функцию калькулятора
    registry.register_function(
        name="my_calculator",
        description="Простой инструмент математических вычислений, поддерживающий основные операции (+,-,*,/) и функцию sqrt.",
        func=my_calculate
    )

    return registry