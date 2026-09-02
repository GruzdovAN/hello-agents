"""StockInsightAgent — Интеллектуальный помощник по биржевому анализу

использование:
интерактивное меню main.py Python
быстрый анализ «проблемы» python main.py (фреймворк ReAct)
python main.py -d Углубленный анализ «Проблемы» (фреймворк PlanSolve)
python main.py -r Критический анализ «проблемы» (отражение структуры)
"""
import sys
from llm_client import HelloAgentsLLM
from agent import StockInsightAgent
from plan_agent import PlanAndSolveStockAgent
from reflection_agent import ReflectionStockAgent
from framework_agent import FrameworkStockAgent
from memory import memory_get_watchlist, memory_get_history
from rag import rag_import, rag_stats


def show_banner():
    print()
    print("  ╔═════════════════════════════════════════════════════════════╗")
    print("  ║                                                             ║")
print(" ║ StockInsightAgent v2.0 Интеллектуальный помощник по анализу акций ║")
    print("  ║                                                             ║")
    print("  ║   数据: akshare 实时行情 + 财务 + 新闻                        ║")
    print("  ║   记忆: 关注列表 | 分析历史 | 用户偏好                         ║")
    print("  ║   知识: 估值体系 | 技术指标 | 风控原则                         ║")
    print("  ║                                                             ║")
    print("  ╚═════════════════════════════════════════════════════════════╝")
    print()


MENU = """
  ┌────────────────────────────────────────────────────────────┐
  │                                                            │
  │  [1]  快速分析        框架 ReAct           ~30秒            │
  │  [2]  深度分析        框架 PlanSolve       ~2分钟            │
  │  [3]  批判分析        框架 Reflection      ~3分钟            │
  │                                                            │
  ├────────────────────────────────────────────────────────────┤
  │                                                            │
  │  [4]  ReAct           手写解析+循环                         │
  │  [5]  PlanSolve       手写规划+执行                         │
  │  [6]  Reflection      手写记忆+反思                         │
  │                                                            │
  ├────────────────────────────────────────────────────────────┤
  │                                                            │
  │  [w]  查看关注列表                                          │
  │  [h]  查看分析历史                                          │
  │  [k]  导入投资文档到知识库                                   │
  │                                                            │
  ├────────────────────────────────────────────────────────────┤
  │                                                            │
  │  [m]  重新显示菜单                                          │
  │  [0]  退出                                                  │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
"""

EXAMPLES = """
Просто введите вопрос, чтобы начать анализ, например:
Акции> Анализ текущей оценки Kweichow Moutai 600519
Акции> Сравните оценки Wuliangye и Moutai

Сначала выберите режим, затем введите вопрос:
Акции > 2 (перейти к углубленному анализу)
Акции> Комплексная оценка BYD 002594
"""


def main():
# ── Режим быстрого доступа к параметрам командной строки ──
    if len(sys.argv) > 1:
        a = FrameworkStockAgent()
        if "-d" in sys.argv:
            sys.argv.remove("-d")
q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("问题: ").strip()
            print(a.plan_solve(q))
        elif "-r" in sys.argv:
            sys.argv.remove("-r")
q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("问题: ").strip()
            print(a.reflect(q))
        else:
            q = " ".join(sys.argv[1:])
            print(a.react(q))
        return

# ── Режим интерактивного меню ──
    show_banner()
    print(MENU)
    print(EXAMPLES)

    fw = FrameworkStockAgent()
mode = "реагировать" #Текущий режим

    while True:
        try:
            q = input("\nStock> ").strip()
        except (EOFError, KeyboardInterrupt):
print("\nДо свидания")
            break

        if not q:
            continue

# Выбор меню
        if q in ("1", "2", "3", "4", "5", "6", "w", "h", "k", "m", "0"):
            if q == "1":
                mode = "react"
                print("  >> 切换到 [快速分析] 模式。输入你的问题:")
            elif q == "2":
                mode = "plan"
print(" >> Переключитесь в режим [Глубокий анализ]. Введите свой вопрос:")
            elif q == "3":
                mode = "reflect"
print(" >> Перейдите в режим [критического анализа]. Введите свой вопрос:")
            elif q == "4":
                mode = "raw-react"
                print("  >> 切换到 [教学版 ReAct] 模式。输入你的问题:")
            elif q == "5":
                mode = "raw-plan"
                print("  >> 切换到 [教学版 PlanSolve] 模式。输入你的问题:")
            elif q == "6":
                mode = "raw-reflect"
                print("  >> 切换到 [教学版 Reflection] 模式。输入你的问题:")
            elif q == "w":
                print(memory_get_watchlist())
            elif q == "h":
                code = input("  股票代码 (回车看全部): ").strip()
                print(memory_get_history(code))
            elif q == "k":
path = input("Путь к документу: ").strip()
                print(rag_import(path))
                print(rag_stats())
            elif q == "m":
                print(MENU)
            elif q == "0":
печать("До свидания")
                break
            continue

# Выполнить анализ
        print()
        if mode == "react":
            print(fw.react(q))
        elif mode == "plan":
            print(fw.plan_solve(q))
        elif mode == "reflect":
            print(fw.reflect(q))
        elif mode == "raw-react":
            StockInsightAgent(HelloAgentsLLM(), max_steps=6).run(q)
        elif mode == "raw-plan":
            PlanAndSolveStockAgent(HelloAgentsLLM()).run(q)
        elif mode == "raw-reflect":
            ReflectionStockAgent(HelloAgentsLLM(), max_iterations=2).run(q)


if __name__ == "__main__":
    main()
