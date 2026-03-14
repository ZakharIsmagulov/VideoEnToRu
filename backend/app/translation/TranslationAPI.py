import logging
import functools
import time
from pathlib import Path
from typing import List, Dict, Literal
import json
from collections.abc import Callable

from app.translation.TranslationConfig import TranslationConfig as Config
from app.translation.audio_extractor import extract_audio
from app.translation.transcriber import transcribe_audio
from app.translation.translator import translate_pipeline

from app.exceptions.TranslationException import *


def retry(max_retries: int, delay: int, error_status: str):
    """
    Decorator for the retry function in classes.

    :param max_retries: Number of the maximum retries.
    :param delay: Delay between retries in ms.
    :param error_status: Error status string to set if exception was raised.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            logger: logging.Logger = self.logger

            for i in range(1, max_retries + 1):
                try:
                    return func(self, *args, **kwargs)
                except PathNotExist as e:
                    logger.error(str(e), exc_info=True)
                    self.status = error_status
                    raise
                except (AudioExtractionError, TranscriptionError) as e:
                    logger.warning(f"Attempt {i}/{max_retries} failed: {str(e)}")
                    if i == max_retries:
                        self.status = error_status
                        raise
                    time.sleep(delay / 1000)
                except Exception as e:
                    logger.error(str(e), exc_info=True)
                    self.status = error_status
                    raise

        return wrapper
    return decorator


class VideoTranslator:
    def __init__(self, video_name: str, should_stop: Callable[[], bool], video_theme: str = "Разговорное видео"):
        self.logger: logging.Logger = logging.getLogger(Config.logger_name)
        self.video_name: str = video_name
        self.video_id: int = int(Path(video_name).stem)
        self.audio_name: str | None = None
        self.transcription: List[Dict] | None = None
        self.translation: List[Dict] | None = None
        self.tts_name: str | None = None
        self.res_name: str | None = None
        self.status: Literal["free", "extracted", "transcribed", "translated", "done", "error", "stopped"] = "free"
        self._should_stop = should_stop

    def _check_stop(self):
        if self._should_stop():
            self.status = "stopped"
            raise TranslationStopped()

    def get_status(self):
        return self.status

    def get_res_name(self):
        return self.res_name

    def clear(self):
        filenames = [
            self.audio_name,
            self.tts_name,
        ]
        for filename in filenames:
            file_path = Config.temp_path / filename
            if file_path.exists():
                file_path.unlink()

    def run(self):
        try:
            self._check_stop()
            self.extract_audio()

            self._check_stop()
            self.transcribe_audio()

            self._check_stop()
            self.translate_segments()

            res_path = (Config.processed_path / Path(f"{self.video_id}.json")).write_text(
                json.dumps(self.translation, indent=2, ensure_ascii=False))

            return res_path
        finally:
            self.clear()



    @retry(3, 10, "error")
    def extract_audio(self):
        """
        Extract audio from the video by using ffmpeg. Saves result in self.audio_path
        """
        video_path = Config.upload_path / self.video_name
        self.audio_name = extract_audio(video_path=video_path,
                                        temp_dir=Config.temp_path,
                                        logger_name=Config.logger_name)
        self.status = "extracted"

        self.logger.info("Extracted audio from video")


    @retry(3, 10, "error")
    def transcribe_audio(self):
        """
        Transcribe audio from self.audio_path. Saves List of Dict with segments in self.transcription
        """
        self.transcription = transcribe_audio(temp_dir=Config.temp_path,
                                              audio_name=self.audio_name,
                                              model_path=Config.transcriber_path,
                                              logger_name=Config.logger_name)
        self.status = "transcribed"

        self.logger.info("Transcribed audio")

    @retry(3, 10, "error")
    def translate_segments(self):
        """
        Translate segments from self.transcription. Saves List of Dict with segments in self.translation
        """
        self.transcription = json.loads((Config.temp_path / "temp_transcription.json").read_text())
        if self.transcription is None:
            raise ValueError("There is no transcription defined")

        self.translation = translate_pipeline(segments=self.transcription,
                                              translator_model_path=Config.translator_path,
                                              formatter_model_path=Config.formatter_path,
                                              prompts_path=Config.prompts_path,
                                              video_theme=Config.video_theme,
                                              logger_name=Config.logger_name)

        self.status = "translated"

        self.logger.info("Translated segments")

    @retry(3, 10, "error")
    def tts(self):
        """
        Voice over original audio by self.translation. Saves result in self.tts
        """
        pass

    @retry(3, 10, "error")
    def attach_audio(self):
        """
        Attach audio to the original video. Saves result in self.res_path
        """
        pass
