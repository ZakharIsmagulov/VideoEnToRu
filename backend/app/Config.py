from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import logging


class Settings(BaseSettings):
    db_url: str

    jwt_secret: str
    jwt_algo: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 15
    jwt_issuer: str
    jwt_audience: str
    token_url: str
    refresh_url: str
    is_secure_cookie: bool

    upload_path: Path = Path("./data/uploads").absolute()
    processed_path: Path = Path("./data/processed").absolute()
    processed_ext: str = ".mp4"

    transcriber_path: Path = Path("translation/models/"
                                  "whisper/medium/snapshots/a29b04bd15381511a9af671baec01072039215e3").absolute()
    translator_path: Path = Path("translation/models/nllb").absolute()
    formatter_path: Path = Path("translation/models/mistral_gguf\Mistral-7B-Instruct-v0.3-Q4_K_M.gguf").absolute()
    temp_path: Path = Path("translation/temp")
    prompts_path: Path = Path("translation/prompts")

    logger_path: Path = Path("./logs").absolute()
    log_to_console: bool = True
    api_logger: str
    pipeline_logger: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
settings.is_secure_cookie = False
# if settings.is_secure_cookie == "False":
#     settings.is_secure_cookie = False
# else:
#     settings.is_secure_cookie = True


api_logger = logging.getLogger(settings.api_logger)
api_logger.setLevel(logging.INFO)
if not settings.log_to_console:
    file_handler = logging.FileHandler(str(settings.logger_path / "api.log"), mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    api_logger.addHandler(file_handler)
api_logger.info("Api logger initialized")

pipeline_logger = logging.getLogger(settings.pipeline_logger)
pipeline_logger.setLevel(logging.INFO)
if not settings.log_to_console:
    file_handler = logging.FileHandler(str(settings.logger_path / "pipeline.log"), mode='a', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    pipeline_logger.addHandler(file_handler)
pipeline_logger.info("Pipeline logger initialized")
