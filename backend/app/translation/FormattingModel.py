import json
import logging
from llama_cpp import Llama
import functools
import time
from typing import Dict
from tqdm import tqdm


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
                    logger.warning(f"Formatting attempt {i}/{max_retries} failed: {str(e)}")
                    if i == max_retries:
                        raise
                    time.sleep(delay / 1000)

        return wrapper
    return decorator


class FormattingModel:
    def __init__(self, model_path: str, logger_name: str):
        self.logger = logging.getLogger(logger_name)

        self.model = Llama(
            model_path=model_path,
            n_ctx=32768,
            n_gpu_layers=-1,  # если OOM — снизьте до 28/24/20
            n_batch=512,  # можно 256 если упирается
            verbose=False
        )

    def _get_prompt(self, sys_prompt: str, user_prompt: str):
        messages = [
                       {"role": "system", "content": sys_prompt},
                       {"role": "user", "content": user_prompt},
                   ]
        return messages

    @retry(2, 10)
    def generate_output(self, sys_prompt: str, user_prompt: str) -> Dict:
        prompt = self._get_prompt(sys_prompt, user_prompt)
        print(prompt)
        stream = self.model.create_chat_completion(
            messages=prompt,
            temperature=0.0,
            stream=True,
            max_tokens=3000
        )

        chunks = []

        progress = tqdm(
            desc="Generating",
            unit="tok",
            leave=False,
        )

        try:
            for chunk in stream:
                delta = chunk["choices"][0].get("delta", {})
                piece = delta.get("content", "")
                if piece:
                    chunks.append(piece)

                    # В streaming-режиме обычно приходит примерно по токену/кусочку.
                    # Это не идеально точный токен-счетчик, но для прогресса подходит.
                    if progress is not None:
                        progress.update(1)
        finally:
            if progress is not None:
                progress.close()

        text = "".join(chunks)
        print(text)
        result = json.loads(text)
        return result
