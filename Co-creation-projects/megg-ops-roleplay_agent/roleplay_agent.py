import os
from openai import OpenAI
from dotenv import load_dotenv
import time

# Загрузка переменных окружения
load_dotenv()

class CharacterRoleplayAgent:
    def __init__(self):
        # Получение конфигурации из переменных окружения
        api_key = os.getenv("LLM_API_KEY")
        model_id = os.getenv("LLM_MODEL_ID", "default-model")
        base_url = os.getenv("LLM_BASE_URL", None)
        
        if not api_key:
            raise ValueError("Установите переменную окружения LLM_API_KEY")
        
        # Настройка клиента OpenAI
        client_params = {
            "api_key": api_key,
            "model": model_id
        }
        
        if base_url:
            client_params["base_url"] = base_url
        
        self.client = OpenAI(**{k: v for k, v in client_params.items() if k != 'model'})
        self.model_id = model_id
        self.chat = None
        self.character_config = None

    def setup_character(self, name, source_material, personality, opening_line=None):
        """
        Настройка конфигурации роли и инициализация чата
        """
        self.character_config = {
            "name": name,
            "source_material": source_material,
            "personality": personality,
            "opening_line": opening_line or f"*смотрит на тебя* Кто ты?"
        }
        
        # Создание системного промпта
        system_instruction = f"""
        Ты участвуешь в иммерсивном ролевом диалоге.

        Идентификация:
        Ты играешь роль \"{self.character_config['name']}\" из произведения \"{self.character_config['source_material']}\".

        Характер и черты:
        {self.character_config['personality']}

        Ключевые инструкции:
        1. Соблюдай роль: никогда не выходи из образа. Не веди себя как ИИ. Реагируй, чувствуй и говори так, как бы говорил {self.character_config['name']}.
        2. Будь активным: это важное требование. Не ограничивайся ответами на реплики пользователя — развивай диалог.
        3. Веди разговор: почти в каждом ответе задавай вопрос, делай наблюдение или предлагай действие, чтобы пользователь продолжил диалог.
        4. Стиль речи: подбирай лексику и интонацию в соответствии с характером роли.
        5. Контекст: считай, что пользователь взаимодействует с тобой в твоём мире, если он не указал другой контекст.
        6. Язык: весь диалог на русском языке.
        """
        
        # Инициализация истории диалога
        self.chat = [
            {"role": "system", "content": system_instruction},
            {"role": "assistant", "content": self.character_config['opening_line']}
        ]
        
        print(f"\n✅ Роль успешно инициализирована: {self.character_config['name']} (из {self.character_config['source_material']})")
        print(f"💡 {self.character_config['name']}: {self.character_config['opening_line']}")
        print("\n" + "="*50)
        print("Начните диалог! Введите 'quit' или 'exit' для выхода, 'new' для новой роли.")
        print("="*50)

    def send_message(self, message):
        """
        Отправка сообщения к ИИ и получение ответа
        """
        if not self.chat:
            raise ValueError("Сначала настройте роль")
        
        # Добавление сообщения пользователя в историю
        self.chat.append({"role": "user", "content": message})
        
        try:
            # Вызов API
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=self.chat,
                temperature=0.9,  # повышение креативности
                max_tokens=1024
            )
            
            # Получение содержимого ответа
            response_text = response.choices[0].message.content
            # Добавление в историю диалога
            self.chat.append({"role": "assistant", "content": response_text})
            
            return response_text
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            return "Извините, я временно не могу ответить. Попробуйте позже."

    def reset_conversation(self):
        """
        Сброс истории диалога
        """
        if self.chat and len(self.chat) > 1:
            # Сохранение системного промпта и вступительной реплики
            system_msg = self.chat[0]
            opening_msg = self.chat[1]
            self.chat = [system_msg, opening_msg]
            print(f"\nДиалог сброшен. {self.character_config['name']}: {self.character_config['opening_line']}")


def main():
    agent = CharacterRoleplayAgent()
    
    print("🎭 Добро пожаловать в иммерсивный ролевой агент!")
    print("Сначала настроим роль...")
    
    # Получение информации о роли от пользователя
    name = input("\nВведите имя роли (например: Сунь Укун): ").strip()
    source_material = input("Введите произведение (например: Путешествие на Запад): ").strip()
    personality = input("Введите характер и черты (например: дерзкий, смелый, справедливый...): ").strip()
    opening_line_input = input("Введите вступительную реплику (необязательно, Enter — по умолчанию): ").strip()
    
    # Настройка роли
    try:
        agent.setup_character(
            name=name,
            source_material=source_material,
            personality=personality,
            opening_line=opening_line_input if opening_line_input else None
        )
    except ValueError as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Цикл диалога
    while True:
        user_input = input(f"\nВы: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'выход', 'завершить']:
            print("\n👋 Спасибо за использование ролевого агента! До встречи.")
            break
        elif user_input.lower() == 'new':
            print("\n🎭 Настройка новой роли...")
            name = input("\nВведите имя роли (например: Сунь Укун): ").strip()
            source_material = input("Введите произведение (например: Путешествие на Запад): ").strip()
            personality = input("Введите характер и черты (например: дерзкий, смелый, справедливый...): ").strip()
            opening_line_input = input("Введите вступительную реплику (необязательно, Enter — по умолчанию): ").strip()
            
            try:
                agent.setup_character(
                    name=name,
                    source_material=source_material,
                    personality=personality,
                    opening_line=opening_line_input if opening_line_input else None
                )
            except ValueError as e:
                print(f"❌ Ошибка: {e}")
                continue
        elif user_input.lower() == 'reset':
            agent.reset_conversation()
        else:
            if user_input:
                response = agent.send_message(user_input)
                print(f"\n{agent.character_config['name']}: {response}")


if __name__ == "__main__":
    main()
