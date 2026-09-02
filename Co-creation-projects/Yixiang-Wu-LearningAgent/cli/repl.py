# cli/repl.py
"""Реализация цикла REPL"""

from hello_agents import HelloAgentsLLM
from core.main_agent import MainAgent
from core.file_manager import FileManager
from utils.logger import setup_logger


def print_welcome():
"""Распечатать приветственное сообщение"""
    print(
        """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           🤖 Welcome to LearningAgent!                   ║
║                                                          ║
║              Your AI Learning Companion                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Введите /help, чтобы просмотреть доступные команды.
    """
    )


def print_goodbye():
"""Распечатать прощальное сообщение"""
    print(
        """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║                  👋 Goodbye!                             ║
║                                                          ║
║              Keep Learning, Keep Growing!                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    )


def start_repl():
    """
Запустить цикл REPL
    """
# Настраиваем журнал
    logger = setup_logger("learning_agent")
    logger.info("LearningAgent started")

#Инициализируем компоненты
    try:
        llm = HelloAgentsLLM()
        file_manager = FileManager()
# REPL всегда является интерактивной средой с включенным потоковым выводом
        agent = MainAgent(llm, file_manager, streaming=True)
    except Exception as e:
print(f"❌ Ошибка инициализации: {e}")
print("Пожалуйста, проверьте файл конфигурации (.env) и ключ API")
        return

# Отображение приветственного сообщения
    print_welcome()

#цикл REPL
    while True:
        try:
# Получить пользовательский ввод
            user_input = input("\n> ").strip()

# Пропустить пустой ввод
            if not user_input:
                continue

# Команды процесса
            result = agent.process_command(user_input)

# Проверяем, выходить ли
            if result == "EXIT":
                print_goodbye()
                logger.info("LearningAgent exited normally")
                break

# показать результаты
            # 注意：如果 agent.streaming=True，流式输出已经打印到 stdout
#Печатать только результаты, не относящиеся к потоковой передаче (например, справочную информацию, сообщения об ошибках и т. д.)
            if not agent.streaming:
                print(result)

        except KeyboardInterrupt:
print("\n\n👋 Операция отменена")
            continue

        except Exception as e:
            logger.error(f"Error in REPL: {e}", exc_info=True)
print(f"❌ Произошла ошибка: {e}")
print("Введите /help, чтобы просмотреть справку, или /exit, чтобы выйти")


if __name__ == "__main__":
    start_repl()
