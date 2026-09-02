import os  # noqa: D100

from pydub import AudioSegment

"""
DeepCast 项目使用 pydub 库将多个 TTS 生成的音频片段（MP3）合成为最终的播客文件。
pydub использует ffmpeg для преобразования и обработки аудиоформатов (особенно экспорта MP3).
Поэтому вы должны убедиться, что ffmpeg установлен в вашей системе и что его путь правильно найден средой Python.
Этот скрипт используется для проверки правильности настройки ffmpeg и возможности вызова из pydub.
"""

#Устанавливаем путь к ffmpeg
ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.converter = ffmpeg_path

def test_ffmpeg():
    print(f"Testing ffmpeg at: {ffmpeg_path}")
    
    # Check if file exists
    if not os.path.exists(ffmpeg_path):
        print(f"❌ Warning: ffmpeg executable not found at {ffmpeg_path}")
    else:
        print("✅ ffmpeg executable found.")
    
    try:
        # 创建 1 秒的静音片段
        print("Creating silent audio segment...")
        silence = AudioSegment.silent(duration=1000)
        
        output_file = "test_ffmpeg_output.mp3"
        print(f"Exporting to {output_file}...")
        
#Экспорт требует ffmpeg
        silence.export(output_file, format="mp3")
        
        if os.path.exists(output_file):
            print("✅ Success! ffmpeg is working correctly.")
            print(f"Output file size: {os.path.getsize(output_file)} bytes")
# Очистить файлы
            os.remove(output_file)
        else:
            print("❌ Failed: Output file was not created.")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        # import traceback
        # traceback.print_exc()

if __name__ == "__main__":
    test_ffmpeg()
