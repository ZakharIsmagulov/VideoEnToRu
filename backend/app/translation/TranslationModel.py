import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import functools
import time


def retry(max_retries: int, delay: int):
    """
    Decorator for the retry function in classes.

    :param max_retries: Number of the maximum retries.
    :param delay: Delay between retries in ms.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            logger: logging.Logger = self.logger

            for i in range(1, max_retries + 1):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    logger.warning(f"Translation attempt {i}/{max_retries} failed: {str(e)}")
                    if i == max_retries:
                        raise
                    time.sleep(delay / 1000)

        return wrapper
    return decorator


class TranslationModel:
    def __init__(self, model_path: str, logger_name: str):
        self.logger = logging.getLogger(logger_name)

        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        self.model.to("cuda").eval()
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.tokenizer.src_lang = "eng_Latn"
        self.forced_bos_token_id = self.tokenizer.convert_tokens_to_ids("rus_Cyrl")

    @retry(2, 10)
    def generate_output(self, text: str) -> str:
        inputs = self.tokenizer(text, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            out = self.model.generate(
                **inputs,
                forced_bos_token_id=self.forced_bos_token_id,
                max_new_tokens=128,
            )
        return self.tokenizer.decode(out[0], skip_special_tokens=True).strip()