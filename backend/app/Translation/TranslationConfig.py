from pathlib import Path


class TranslationConfig:
    def __init__(self,
                 logger_name: str,
                 logger_path: Path,
                 abs_data_path: Path,
                 whisper_model: str = r"whisper\medium\snapshots\a29b04bd15381511a9af671baec01072039215e3",
                 translator_model: str = r"nllb",
                 formatter_model: str = r"mistral_gguf\Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
                 temp_dir: str = "temp",
                 video_theme: str = "Американский ситком",
                 ):
        self.logger_name = logger_name
        self.logger_path = logger_path / Path(logger_name + ".log")
        self.logger_path.unlink(missing_ok=True)
        self.abs_data_path = Path(abs_data_path)
        self.temp_dir = Path("Translation") / temp_dir
        self.transcriber_model_path = Path("Translation") / "models" / whisper_model
        self.translator_model_path = Path("Translation") / "models" / translator_model
        self.formatter_model_path = Path("Translation") / "models" / formatter_model
        self.prompts_path = Path("Translation") / "prompts"
        self.video_theme = video_theme
