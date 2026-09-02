"""
Gradio-интерфейс — мультиагентная система советов по одежде по погоде
Сервис доступен локально на порту 8899
"""
import gradio as gr
import sys
import os

# Добавление текущей директории в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_weather_and_fashion_advice(city_name):
    """
    Получить погоду и рекомендации по одежде для указанного города
    :param city_name: название города
    :return: полный текст ответа
    """
    try:
        # Импорт мультиагентного координатора
        from multi_agent_coordinator import MultiAgentCoordinator
        
        # Создание экземпляра координатора
        coordinator = MultiAgentCoordinator()
        
        # Формирование запроса
        query = f"Запросить погоду в городе {city_name} и дать рекомендации по одежде"
        
        # Обработка запроса
        result = coordinator.process_query(query)
        
        # Возврат полного текста ответа
        response_text = f"""
🏙️ **Город запроса**: {city_name}
🔍 **Запрос**: {query}

📊 **Результат совместной работы агентов**:
{result}

💡 **О системе**:
- Система использует мультиагентную архитектуру
- Агент погоды получает данные
- Агент одежды даёт рекомендации по погоде
- Координатор управляет коммуникацией и задачами
"""
        
        return response_text
        
    except Exception as e:
        # Если мультиагентная система недоступна — упрощённая версия
        try:
            from simple_multi_agent import get_real_weather, get_llm_fashion_advice
            
            # Получение погодной информации
            weather_info, weather_details = get_real_weather(city_name)
            
            # Получение рекомендаций LLM по одежде
            fashion_advice = get_llm_fashion_advice(weather_details, city_name)
            
            response_text = f"""
🏙️ **Город запроса**: {city_name}

📊 **Информация о погоде**:
{weather_info}

🤖 **Рекомендации LLM по одежде**:
{fashion_advice}

💡 **О системе**:
- Упрощённая мультиагентная система
- Рекомендации на основе реальных данных погоды
- LLM обрабатывает рекомендации по одежде
"""
            return response_text
            
        except Exception as e2:
            # Если все методы завершились ошибкой — сообщение об ошибке
            error_text = f"""
❌ **Ошибка системы**: Не удалось получить данные для {city_name} — погода и рекомендации по одежде

**Сообщение об ошибке**:
- Основная ошибка: {str(e)}
- Резервная ошибка: {str(e2)}

💡 **Решение**:
1. Проверьте сетевое подключение
2. Убедитесь, что API погоды доступен
3. Проверьте установку зависимостей

🔧 **Альтернатива**:
Попробуйте: Пекин, Шанхай, Гуанчжоу, Шэньчжэнь, Ханчжоу, Чэнду
"""
            return error_text

def create_gradio_interface():
    """Создание Gradio-интерфейса"""
    
    # Описание интерфейса
    description = """
    # 🌤️ Мультиагентная система советов по одежде по погоде
    
    Введите город — система предоставит:
    - 📊 Актуальную погоду
    - 🤖 Рекомендации LLM по одежде
    - 💡 Профессиональные советы по стилю
    
    **Возможности**:
    - Мультиагентная обработка
    - Запрос реальных данных погоды
    - ИИ-рекомендации по одежде
    - Поддержка многоходового диалога
    """
    
    # Создание интерфейса
    with gr.Blocks(
        title="Мультиагентная система советов по одежде по погоде",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 900px !important;
        }
        .output-text {
            font-size: 14px;
            line-height: 1.6;
        }
        """
    ) as demo:
        
        gr.Markdown(description)
        
        with gr.Row():
            with gr.Column(scale=1):
                city_input = gr.Textbox(
                    label="🌍 Введите название города",
                    placeholder="Например: Пекин, Шанхай, Гуанчжоу, Шэньчжэнь...",
                    info="Поддерживаются русские и английские названия"
                )
                
                submit_btn = gr.Button(
                    "🚀 Получить рекомендации",
                    variant="primary",
                    size="lg"
                )
                
                clear_btn = gr.Button("🗑️ Очистить", variant="secondary")
                
            with gr.Column(scale=2):
                output_text = gr.Textbox(
                    label="📋 Полный ответ",
                    lines=20,
                    max_lines=30,
                    show_copy_button=True,
                    elem_classes="output-text"
                )
        
        # Примеры городов
        examples = gr.Examples(
            examples=[["beijing"], ["tokoy"], ["london"], ["new york"], ["paris"], ["seoul"], ["bangkok"], ["harbin"]],
            inputs=city_input,
            label="💡 Нажмите пример для быстрого теста"
        )
        
        # Обработчики кнопок
        submit_btn.click(
            fn=get_weather_and_fashion_advice,
            inputs=city_input,
            outputs=output_text
        )
        
        clear_btn.click(
            fn=lambda: "",
            inputs=[],
            outputs=output_text
        )
        
        # Отправка по Enter
        city_input.submit(
            fn=get_weather_and_fashion_advice,
            inputs=city_input,
            outputs=output_text
        )
        
        # Информация в подвале
        gr.Markdown("""
        ---
        
        ### 🔧 Информация о системе
        - **Версия**: v1.0.0
        - **Архитектура**: Мультиагентная система
        - **Стек**: Python + Gradio + мультиагентный фреймворк
        - **Порт**: 8899
        
        ### 📖 Инструкция
        1. Введите город в поле слева
        2. Нажмите «Получить рекомендации» или Enter
        3. Смотрите полный ответ справа
        4. Используйте примеры для разных городов
        
        ### 🎯 Особенности
        - 🌤️ Запрос актуальных данных о погоде
        - 🤖 ИИ-рекомендации по одежде
        - 🔄 Мультиагентная обработка
        - 📱 Адаптивный веб-интерфейс
        - 🎨 Удобный интерфейс
        """)
    
    return demo

def main():
    """Запуск Gradio-приложения"""
    print("🚀 Запуск системы советов по одежде — Gradio")
    print("🌐 Адрес: http://localhost:8899")
    print("⏳ Запуск сервиса...")
    
    # Создание интерфейса
    demo = create_gradio_interface()
    
    # Запуск сервиса
    demo.launch(
        server_name="0.0.0.0",
        server_port=8899,
        share=False,
        show_error=True,
        debug=True,
        quiet=False
    )

if __name__ == "__main__":
    main()
