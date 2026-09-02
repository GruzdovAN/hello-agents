"""Сервис, объединяющий аудиоклипы в один файл подкаста."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from pydub import AudioSegment

from config import Configuration

logger = logging.getLogger(__name__)


class PodcastSynthesisService:
"""Объедините несколько аудиоклипов в окончательный файл подкаста."""

    def __init__(self, config: Configuration) -> None:
        """
Инициализируйте службу синтеза звука.

        Args:
config: объект конфигурации, содержащий путь к ffmpeg и выходной путь.
        """
        self._config = config
        self._output_dir = Path(config.audio_output_dir)
        
# Если указан путь ffmpeg, настройте его
        if config.ffmpeg_path:
            AudioSegment.converter = config.ffmpeg_path
            logger.info("Configured ffmpeg path: %s", config.ffmpeg_path)
        
        # 确保 pydub/ffmpeg 可用 - 假设 ffmpeg 已安装在系统中
# В противном случае pydub может выдать предупреждение или потерпеть неудачу, но мы перехватим исключение.

    def synthesize_podcast(self, audio_files: list[str], task_id: str = "default", cancel_check: Callable[[], bool] | None = None) -> str | None:
        """
Объедините аудиофайлы в один подкаст MP3.

        Args:
audio_files: упорядоченный список путей к входным аудиофайлам.
Task_id: уникальный идентификатор имени выходного файла.
            cancel_check: 可选的取消检查回调，返回 True 表示已取消。

        Returns:
Путь к окончательному файлу подкаста или «Нет» в случае ошибки.
        """
        if not audio_files:
            logger.warning("No audio files provided for synthesis.")
            return None

        try:
            combined = AudioSegment.empty()
            
# Тишина между клипами (например, 500 мс)
            silence = AudioSegment.silent(duration=500)

            valid_segments_count = 0
            for file_path in audio_files:
# Проверьте, отменено ли
                if cancel_check and cancel_check():
                    logger.info("Podcast synthesis cancelled.")
                    return None
                    
                path = Path(file_path)
                if not path.exists():
                    logger.warning("Audio file not found: %s", file_path)
                    continue
                
                try:
                    segment = AudioSegment.from_file(file_path, format="mp3")
                    if valid_segments_count > 0:
                        combined += silence
                    combined += segment
                    valid_segments_count += 1
                except Exception as e:
                    logger.error("Failed to load audio segment %s: %s", file_path, e)

            if valid_segments_count == 0:
                logger.error("No valid audio segments to combine.")
                return None

            output_filename = f"podcast_{task_id}.mp3"
            output_path = self._output_dir / output_filename
            
# экспорт
            logger.info("Exporting podcast to %s...", output_path)
            combined.export(output_path, format="mp3")
            
            return str(output_path)

        except Exception as e:
            logger.exception("Podcast synthesis failed: %s", e)
            return None
