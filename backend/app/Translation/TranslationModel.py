class TranslationModel:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def generate_output(self, sys_prompt: str, user_prompt: str) -> str:
        pass