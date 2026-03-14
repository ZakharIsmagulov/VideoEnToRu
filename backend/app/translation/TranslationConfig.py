from pathlib import Path
from pydantic import BaseModel
from app.Config import settings


class TranslationConfig(BaseModel):
    logger_name: str = settings.pipeline_logger

    transcriber_path: Path = settings.transcriber_path
    translator_path: Path = settings.translator_path
    formatter_path: Path = settings.formatter_path

    upload_path: Path = settings.upload_path
    processed_path: Path = settings.processed_path
    temp_path: Path = settings.temp_path
    prompts_path: Path = settings.prompts_path
