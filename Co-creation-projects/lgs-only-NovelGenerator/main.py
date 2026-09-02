import os
import time
import sys
# Добавляем текущую директорию в sys.path для корректных импортов
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "agents")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from agents.outline_agent import OutlineAgent
from agents.chapter_generate_agent import ChapterGenerateAgent
from hello_agents import HelloAgentsLLM

def print_step(step_name):
    print("\n" + "="*60)
    print(f"Выполняется шаг: {step_name}")
    print("="*60 + "\n")

def main():
    # Конфигурация
    novel_id = f"test_novel_{int(time.time())}"
    title = "Тестовый роман для проверки агента"
    user_idea = "История о программисте ИИ, который неожиданно попадает в мир своего собственного кода и должен исправить баги этого мира, чтобы вернуться в реальность."
    
    print(f"Конфигурация теста:\nID романа: {novel_id}\nНазвание: {title}\nИдея: {user_idea}\n")

    # Инициализация LLM
    # Предполагается, что переменные окружения настроены для провайдера по умолчанию
    try:
        llm = HelloAgentsLLM()
        print("LLM инициализирован успешно.")
    except Exception as e:
        print(f"Ошибка инициализации LLM: {e}")
        return

    # ---------------------------------------------------------
    # Тест OutlineAgent
    # ---------------------------------------------------------
    print_step("1. Инициализация OutlineAgent (агент генерации плана)")
    try:
        outline_agent = OutlineAgent(name="TestOutlineAgent", llm=llm)
        print("OutlineAgent инициализирован.")
    except Exception as e:
        print(f"Ошибка инициализации OutlineAgent: {e}")
        return

    print_step("2. Генерация плана (Generate Outline)")
    print(f"Вызов outline_agent.run с идеей: {user_idea}")
    start_time = time.time()
    
    try:
        outline_content, outline_note_id = outline_agent.run(
            user_input=user_idea,
            novel_id=novel_id,
            title=title,
            tags=["научная фантастика", "путешествие во времени", "программист"],
            target_length=1000  # Короткий объём для теста
        )
    except Exception as e:
        print(f"Ошибка генерации плана: {e}")
        return

    end_time = time.time()
    print(f"Генерация плана заняла: {end_time - start_time:.2f} сек.")
    print(f"ID заметки с планом: {outline_note_id}")
    print("Предпросмотр плана (первые 500 символов):")
    print("-" * 30)
    print(outline_content[:500] + "...")
    print("-" * 30)

    # ---------------------------------------------------------
    # Тест ChapterGenerateAgent
    # ---------------------------------------------------------
    print_step("3. Инициализация ChapterGenerateAgent (агент генерации глав)")
    try:
        chapter_agent = ChapterGenerateAgent(
            name="TestChapterAgent", 
            llm=llm,
            max_steps=3,  # Ограничение шагов для теста
            chapter_length=1000  # Короткий объём
        )
        print("ChapterGenerateAgent инициализирован.")
    except Exception as e:
        print(f"Ошибка инициализации ChapterGenerateAgent: {e}")
        return

    print_step("4. Генерация первой главы (Generate Chapter 1)")
    print("Вызов chapter_agent.run для генерации первой главы...")
    start_time = time.time()
    
    try:
        chapter_data, chapter_note_id = chapter_agent.run(
            user_input="Глава 1: герой просыпается в лесу, состоящем из кода.",
            novel_id=novel_id,
            novel_title=title
        )
    except Exception as e:
        print(f"Ошибка генерации главы: {e}")
        return
    
    end_time = time.time()
    print(f"Генерация первой главы заняла: {end_time - start_time:.2f} сек.")
    print(f"ID заметки с главой: {chapter_note_id}")
    print(f"Название главы: {chapter_data.get('title')}")
    print(f"Краткое содержание: {chapter_data.get('summary')}")
    print("Предпросмотр главы (первые 500 символов):")
    print("-" * 30)
    print(chapter_data.get('content', '')[:500] + "...")
    print("-" * 30)

    # ---------------------------------------------------------
    # Проверка
    # ---------------------------------------------------------
    print_step("5. Проверка выходных файлов (Verify Output Files)")
    outline_path = os.path.join("outputs", f"{title}-{novel_id}", "outline")
    chapter_path = os.path.join("outputs", f"{title}-{novel_id}", "chapters")
    
    print(f"Проверка каталога плана: {outline_path}")
    if os.path.exists(outline_path) and os.listdir(outline_path):
        print("PASS: Каталог плана существует и не пуст.")
    else:
        print("FAIL: Каталог плана отсутствует или пуст.")

    print(f"Проверка каталога глав: {chapter_path}")
    if os.path.exists(chapter_path) and os.listdir(chapter_path):
        print("PASS: Каталог глав существует и не пуст.")
    else:
        print("FAIL: Каталог глав отсутствует или пуст.")

    print("\n" + "="*60)
    print("Тестовый процесс завершён")
    print("="*60)

if __name__ == "__main__":
    main()
