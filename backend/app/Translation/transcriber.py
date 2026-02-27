import logging
from .TranslationException import PathNotExist, TranscriptionError
import whisper
from pathlib import Path
from typing import List, Dict


def transcribe_audio(audio_path: Path, model_path: Path,
                     logger_name: str) -> List[Dict]:
    """
    Transcribes an audio file using OpenAI Whisper model.

    :param audio_path: Path to the audio file.
    :param model_path: Path to the Whisper model to use.
    :param logger_name: Name of the logger to use for logging.
    :return: A list of segments with text and timestamps.
    """
    logger = logging.getLogger(logger_name)
    if not audio_path.exists():
        raise PathNotExist(f"Error: Audio file not found at {str(audio_path)}")

    try:
        logger.info(f"Loading Whisper model '{model_path}'...")
        model = whisper.load_model(str(model_path.absolute()), device="cuda")
        
        logger.info(f"Starting transcription for {str(audio_path)}...")
        # The `word_timestamps=True` option can be very useful for more granular control later.
        # For now, we'll stick to segment-level timestamps which is the default.
        result = model.transcribe(str(audio_path.absolute()), verbose=False)
        logger.info("Transcription completed successfully.")

        # Each segment is a dictionary with 'start', 'end', and 'text'.
        return result['segments']

    except Exception as e:
        raise TranscriptionError(f"An error occurred during transcription: {str(e)}")
