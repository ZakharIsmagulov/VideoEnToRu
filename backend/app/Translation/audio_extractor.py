import logging
from .TranslationException import PathNotExist, AudioExtractionError
from pathlib import Path
from moviepy import VideoFileClip


def extract_audio(video_path: Path, temp_dir: Path,
                  logger_name: str) -> Path:
    """
    Extracts audio from a video file and saves it as a WAV file.

    :param video_path: Path to the input video file.
    :param temp_dir: Directory to save the temporary audio file.
    :param logger_name: Name of the logger.
    :return: Path to the extracted audio file.
    """
    logger = logging.getLogger(logger_name)
    if not video_path.exists():
        raise PathNotExist(f"Error: Video file not found at {str(video_path)}")

    try:
        logger.info(f"Starting audio extraction from {str(video_path)}")

        temp_dir.mkdir(parents=True, exist_ok=True)

        # Define the output path for the audio file
        file_basename = video_path.stem
        audio_basename = f"{file_basename}_audio.wav"
        audio_path = temp_dir / audio_basename

        video_clip = VideoFileClip(video_path)
        # Whisper works best with 16kHz mono WAV files.
        # codec='pcm_s16le' ensures it's a standard WAV file.
        video_clip.audio.write_audiofile(
            audio_path, 
            fps=16000, 
            nbytes=2, 
            codec='pcm_s16le'
        )
        video_clip.close()
        logger.info(f"Audio extracted successfully to {str(audio_path)}")
        return audio_path
        
    except Exception as e:
        # Clean up a potentially partially created audio file
        if 'audio_path' in locals() and audio_path.exists():
            audio_path.unlink()
        raise AudioExtractionError(f"Error during audio extraction: {str(e)}")
