import logging
import functools
import time
from .TranslationConfig import TranslationConfig
from .TranslationException import *
from .audio_extractor import extract_audio
from .transcriber import transcribe_audio
from pathlib import Path
from typing import List, Dict, Literal


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
    def __init__(self, config: TranslationConfig):
        self.config = config
        self.logger: logging.Logger = logging.getLogger(config.logger_name)
        self.logger.info("Translator initialized")
        self.audio_path: Path | None = None
        self.transcription: List[Dict] | None = None
        self.translation = None # TODO: Define type of the variable
        self.tts_path: Path | None = None
        self.res_path: Path | None = None
        self.status: Literal["free", "extracted", "transcribed", "translated", "done", "error"] = "free"

    def get_status(self):
        return self.status

    def get_res_path(self):
        return self.res_path

    def clear(self):
        for item in self.config.temp_dir.iterdir():
            if item.is_file():
                item.unlink()
        self.audio_path = None
        self.transcription = None
        self.translation = None
        self.tts_path = None
        self.res_path = None
        self.status = "free"

    @retry(3, 10, "error")
    def extract_audio(self, video_name: str):
        """
        Extract audio from the video by using ffmpeg. Saves result in self.audio_path

        :param video_name: Name of the video file with extension.
        """
        video_path = self.config.abs_data_path / Path("uploads") / video_name
        self.audio_path = extract_audio(video_path=video_path,
                                        temp_dir=self.config.temp_dir,
                                        logger_name=self.config.logger_name)
        self.status = "extracted"

        self.logger.info("Extracted audio from video")


    @retry(3, 10, "error")
    def transcribe_audio(self):
        """
        Transcribe audio from self.audio_path. Saves List of Dict with segments in self.transcription
        """
        if self.audio_path is None:
            raise PathNotExist("There is no audio_path defined")

        self.transcription = transcribe_audio(audio_path=self.audio_path,
                                              model_path=self.config.transcriber_model_path,
                                              logger_name=self.config.logger_name)
        self.status = "transcribed"

        self.logger.info("Transcribed audio")

    @retry(3, 10, "error")
    def translate_segments(self):
        """
        Translate segments from self.transcription. Saves TODO
        """
        pass

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
