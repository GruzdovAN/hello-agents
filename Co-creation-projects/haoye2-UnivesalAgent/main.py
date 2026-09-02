from dotenv import load_dotenv
from src.agents.agent_universal import UniversalAgent

load_dotenv()  # Читаем конфигурацию из .env (параметры LLM)

def main():
    try:
        agent = UniversalAgent()
        print("🤖 Hello-Agents универсальный агент запущен!\n(введите 'exit' или 'quit' для выхода)")

        while True:
            try:
                user_input = input("\nВведите ваш вопрос:").strip()
                
                # Обработка пустого ввода
                if not user_input:
                    print("⚠️  Введите корректный вопрос или команду")
                    continue
                
                # Проверка выхода
                if user_input.lower() in ("exit", "quit"):
                    print("\n👋 До свидания!")
                    break
                
                # Вызов агента
                output = agent.run(user_input)
                print("\nAI >\n", output)
                
            except KeyboardInterrupt:
                print("\n\n👋 Прервано пользователем, до свидания!")
                break
            except Exception as e:
                print(f"\n❌ Ошибка обработки: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Не удалось инициализировать агента: {e}")
        print("💡 Проверьте файл .env и настройки LLM API")

if __name__ == "__main__":
    main()
