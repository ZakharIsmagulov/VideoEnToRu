from pathlib import Path


class TranslationConfig:
    def __init__(self,
                 logger_name: str,
                 logger_path: Path,
                 abs_data_path: Path,
                 whisper_model: str = r"whisper\medium\snapshots\a29b04bd15381511a9af671baec01072039215e3",
                 translator_model: str = r"qwen\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
                 temp_dir: str = "temp",
                 video_theme: str = "",
                 ):
        self.logger_name = logger_name
        self.logger_path = logger_path / Path(logger_name + ".log")
        self.logger_path.unlink(missing_ok=True)
        self.abs_data_path = Path(abs_data_path)
        self.temp_dir = Path("Translation") / Path(temp_dir)
        self.transcriber_model_path = Path("Translation") / Path("models") / Path(whisper_model)
        self.translator_model_path = Path("Translation") / Path("models") / Path(translator_model)
        self.prompts_path = Path("Translation") / Path("prompts")
        self.video_theme = video_theme
