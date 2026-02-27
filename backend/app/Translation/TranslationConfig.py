from pathlib import Path


class TranslationConfig:
    def __init__(self,
                 logger_name: str,
                 abs_data_path: Path,
                 whisper_model: str = "whisper_medium/medium.en.pt",
                 temp_dir: str = "temp",
                 ):
        self.logger_name = logger_name
        self.abs_data_path = Path(abs_data_path)
        self.temp_dir = Path("Translation") / Path(temp_dir)
        self.transcriber_model_path = Path("Translation") / Path("models") / Path(whisper_model)
