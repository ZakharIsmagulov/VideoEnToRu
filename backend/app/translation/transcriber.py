import json
import logging
from app.exceptions.TranslationException import PathNotExist, TranscriptionError
import whisperx
from pathlib import Path
from typing import List, Dict
import gc
import torch


def transcribe_audio(temp_dir: Path, audio_name: str, model_path: Path,
                     logger_name: str) -> List[Dict]:
    """
    Transcribes an audio file using OpenAI Whisper model.

    :param temp_dir: Path to the temp folder.
    :param audio_name: Name of the audiofile in temp_path to transcribe.
    :param model_path: Path to the Whisper model to use.
    :param logger_name: Name of the logger.
    :return: A list of segments with text and timestamps.
    """
    logger = logging.getLogger(logger_name)

    audio_path = temp_dir / audio_name
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
        save_path = temp_dir / "temp_transcription.json"
        logger.info(f"Saving transcription to {str(save_path)}")
        save_path.write_text(json.dumps(result["segments"], ensure_ascii=False, indent=2))
        logger.info(f"Transcription is saved to {str(save_path)}")
        return result["segments"]

    except Exception as e:
        raise TranscriptionError(f"An error occurred during transcription: {str(e)}")
