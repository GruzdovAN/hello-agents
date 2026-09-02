# main.py

import threading
import time
import gradio as gr
import json
from src.agents.sleep_agent import sleep_agent
from src.agents.mind_echo_agent import create_mind_echo_agent

# Запускаем службу SleepAgent A2A (фоновый поток)
threading.Thread(target=lambda: sleep_agent.run(port=6000), daemon=True).start()
time.sleep(1)

mind_agent = create_mind_echo_agent()

def extract_music_info(response_text):
"""Извлечение музыкальной информации из ответов агента"""
    try:
# Попробуйте найти музыкальные данные в формате JSON
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)

            if "tracks" in data and data["tracks"]:
# Извлекаем информацию о первой песне
                first_track = data["tracks"][0]
                return {
                    "title": first_track.get("title", "未知歌曲"),
                    "artist": first_track.get("artist", "未知艺术家"),
                    "playlist_count": data.get("total_tracks", 0),
                    "mood": data.get("mood", ""),
                    "full_data": data
                }
    except:
        pass

# Если музыкальные данные не найдены, верните информацию по умолчанию
    return {
"title": "Рекомендации по музыке для релаксации",
        "artist": "MindEchoAI",
        "playlist_count": 3,
"настроение": "расслабиться"
    }

def chat(user_input: str):
"""Обработка ввода пользователя и возврат ответа"""
    response = mind_agent.run(user_input)
    music_info = extract_music_info(response)

# Возвращаем текст ответа и информацию о музыке
    return response, music_info

def update_music_player(music_info):
"""Обновить дисплей музыкального проигрывателя"""
    if not music_info:
        return gr.update(visible=False), gr.update(visible=False)

# Создайте плеер для отображения текста
    player_text = f"""
🎵 **Сейчас играет: {music_info['title']}**
👤 Исполнитель: {music_info['artist']}
💫 Настроение: {music_info['mood']}
📊 Плейлист: {music_info['playlist_count']} песни

*Примечание: это проигрыватель-симулятор, настоящий музыкальный сервис необходимо интегрировать позже*
    """

    return gr.update(value=player_text, visible=True), gr.update(visible=True)

with gr.Blocks(
title="MindEchoAgent·Эхо настроения",
    theme=gr.themes.Soft(),
    css="""
    .music-player {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin-top: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .music-player h3 {
        margin-top: 0;
        color: white;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 8px;
    }
    .player-controls {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-top: 12px;
    }
    .player-controls button {
        background: rgba(255,255,255,0.2);
        border: none;
        border-radius: 50%;
        width: 44px;
        height: 44px;
        cursor: pointer;
        color: white;
        font-size: 18px;
        transition: all 0.3s ease;
    }
    .player-controls button:hover {
        background: rgba(255,255,255,0.3);
        transform: scale(1.05);
    }
    """
) as demo:

# область заголовка
    gr.Markdown("""
# 🧠🎵 MindEchoAgent · Эхо настроения
### Эмоциональное общение + рекомендации по музыке + повышение уровня эксперта по сну при необходимости
    """)

    with gr.Row():
        with gr.Column(scale=2):
# Область ввода
            with gr.Group():
gr.Markdown("### 💭 Поделитесь своим настроением")
                inp = gr.Textbox(
                    label="",
                    placeholder="例如：我最近晚上睡不着，很焦虑... 或者 需要一些放松的音乐",
                    lines=3,
                    container=False
                )

# кнопка отправки
            btn = gr.Button("✨ 发送", variant="primary", size="lg")

#Область вывода ответа
            with gr.Group():
gr.Markdown("### 🤖 AI echo")
                out = gr.Textbox(
                    label="",
                    lines=8,
                    interactive=False,
                    container=False,
                    show_copy_button=True
                )

        with gr.Column(scale=1):
# Панель музыкального проигрывателя
gr.Markdown("### 🎧 Рекомендация музыки")

#музыкальный плеер
            music_player = gr.HTML(
value="<div style='text-align: center; padding: 20px; color: #666;'>Ожидание рекомендуемой музыки...</div>",
                visible=False,
                elem_classes="music-player"
            )

# Кнопки управления плеером (скрытые, управляются через JavaScript)
            player_controls = gr.HTML("""
            <div class="player-controls" style="display: none;">
                <button onclick="playerControl('prev')">⏮️</button>
                <button onclick="playerControl('play')">▶️</button>
                <button onclick="playerControl('pause')">⏸️</button>
                <button onclick="playerControl('next')">⏭️</button>
                <button onclick="playerControl('volume_up')">🔊</button>
                <button onclick="playerControl('volume_down')">🔉</button>
            </div>
            """, visible=False)

# Логика взаимодействия
    btn.click(
        fn=chat,
        inputs=inp,
        outputs=[out, music_player]
    ).then(
        fn=update_music_player,
        inputs=music_player,
        outputs=[music_player, player_controls]
    )

# Функция управления JavaScript
    demo.load(
        fn=None,
        inputs=None,
        outputs=None,
    )

# Пример ввода
    gr.Examples(
        examples=[
[«Я сегодня так напряжен на работе, хочу послушать расслабляющую музыку»],
["Я очень счастлива и хочу энергичную песню"],
["Не могу спать по ночам, немного волнуюсь"],
[«Фоновая музыка, требующая концентрации на работе»],
            ["运动时想听兴奋的音乐"]
        ],
        inputs=inp,
        outputs=[out, music_player],
        fn=chat,
        cache_examples=True,
label="💡 быстрый пример"
    )

# нижний колонтитул
    gr.Markdown("---")
    gr.Markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.9em;">
        🎵 用AI感知情绪，用音乐温暖心灵 · MindEchoAgent v1.0<br>
⚠️ Воспроизведение музыки — это демонстрация моделирования, а реальную функцию воспроизведения необходимо интегрировать позже.
        </div>
        """
    )

if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
