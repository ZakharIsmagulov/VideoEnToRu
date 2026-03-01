import logging
from .TranslationException import PathNotExist, TranscriptionError
import whisperx
from pathlib import Path
from typing import List, Dict
import gc
import torch


def transcribe_audio(audio_path: Path, model_path: Path,
                     logger_name: str) -> List[Dict]:
    """
    Transcribes an audio file using OpenAI Whisper model.

    :param audio_path: Path to the audio file.
    :param model_path: Path to the Whisper model to use.
    :param logger_name: Name of the logger.
    :return: A list of segments with text and timestamps.
    """
    logger = logging.getLogger(logger_name)
    if not audio_path.exists():
        raise PathNotExist(f"Error: Audio file not found at {str(audio_path)}")

    try:
        logger.info(f"Loading Whisper model '{str(model_path)}'")
        device = "cuda"
        model = whisperx.load_model(str(model_path.absolute()), device, compute_type="float16", language="en")
        logger.info(f"Whisper model '{str(model_path)}' was loaded")

        logger.info(f"Starting transcription for {str(audio_path)}")
        audio = whisperx.load_audio(str(audio_path))
        result = model.transcribe(audio, batch_size=8, verbose=False)
        gc.collect()
        torch.cuda.empty_cache()
        del model
        logger.info("Text segments were made successfully")

        # TODO: 1. Add male/female alignment to the segments
        # TODO: 2. Add diarization with

        # Each segment is a dictionary with 'start', 'end', and 'text'.
        return result['segments']

    except Exception as e:
        raise TranscriptionError(f"An error occurred during transcription: {str(e)}")
