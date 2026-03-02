import json
import logging
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams
import functools
import time
from typing import Dict


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
                    logger.warning(f"Attempt {i}/{max_retries} failed: {str(e)}")
                    if i == max_retries:
                        raise
                    time.sleep(delay / 1000)

        return wrapper
    return decorator


class FormattingModel:
    def __init__(self, model_path: str, logger_name: str):
        self.logger = logging.getLogger(logger_name)

        self.model = LLM(model=model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        response_schema = {"type": "array",
                           "items": {
                               "type": "object",
                               "additionalProperties": False,
                               "properties": {
                                   "phrase_id": {"type": "integer"},
                                   "translated": {"type": "string"},
                               },
                               "required": ["phrase_id", "translated"],
                           },
                           }
        structured = StructuredOutputsParams(json=response_schema)
        self.params = SamplingParams(
            temperature=0.2,
            max_tokens=512,  # важно дать достаточно токенов, чтобы JSON успел закрыться
            structured_outputs=structured,
        )

    def _get_prompt(self, sys_prompt: str, user_prompt: str):
        messages = [
                       {"role": "system", "content": sys_prompt},
                       {"role": "user", "content": user_prompt},
                   ]
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    @retry(2, 10)
    def generate_output(self, sys_prompt: str, user_prompt: str) -> Dict:
        prompt = self._get_prompt(sys_prompt, user_prompt)
        out = self.model.generate([prompt], self.params)
        text = out[0].outputs[0].text
        result = json.loads(text)
        return result
