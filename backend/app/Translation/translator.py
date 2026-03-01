import logging
from llama_cpp import Llama
from typing import List, Dict
from pathlib import Path
import math
import json
from pydantic import BaseModel, create_model
import time
from tqdm import tqdm


class SegmentTranslation(BaseModel):
    translated: str


def get_prompt(prompt: str, **kwargs) -> str:
    for key, val in kwargs.items():
        prompt = prompt.replace(f"%{key.upper()}%", str(val))
    return prompt

def make_user_prompt(prompt: str,
                     to_translate: List[Dict[str, Dict]],
                     prev_cont: List[Dict[str, Dict]] = None,
                     future_cont: List[Dict[str, Dict]] = None) -> str:
    if prev_cont is None:
        prev = "NO PREVIOUS CONTEXT"
    else:
        items = [item.items() for item in prev_cont]
        prev = ' '.join([val['text'] for item in items for _, val in item])
    if future_cont is None:
        future = "NO FUTURE CONTEXT"
    else:
        items = [item.items() for item in future_cont]
        future = ' '.join([val['text'] for item in items for _, val in item])
    texts = {k: v for d in to_translate for k, v in d.items()}
    json_to_translate = json.dumps(texts, indent=2, ensure_ascii=False)
    return get_prompt(prompt, PREV_CONTEXT=prev, FUTURE_CONTEXT=future, JSON_TO_TRANSLATE=json_to_translate)


def generate(model,
             messages,
             schema) -> str:
    response_stream = model.create_chat_completion(
        messages=messages,
        response_format={
            "type": "json_object",
            "schema": schema
        },
        temperature=0.1,
        stream=True
    )

    result_text = ""
    for chunk in tqdm(response_stream, desc=f"Генерация батча", unit=" ток"):
        delta = chunk["choices"][0]["delta"]
        if "content" in delta:
            content = delta["content"]
            result_text += content

    # result_text = response["choices"][0]["message"]["content"]

    return result_text


def parse_result(json_string: str, batch: List[Dict[str, Dict]], segments: List[Dict],
                 logger: logging.Logger) -> List[Dict]:
    results = []
    try:
        translations = json.loads(json_string, strict=False)
        for idx, item in enumerate(batch):
            segment_key = list(item.keys())[0]
            segment_data = translations[segment_key]
            translated_text = segment_data["translated"]

            results.append({
                "start": segments[idx]["start"],
                "end": segments[idx]["end"],
                "text": translated_text
            })
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON. LLM output: {json_string}")
        raise
    return results


def translate_segments(segments: List[Dict], model_path: Path, prompts_path: Path, video_theme: str,
                       logger_name: str) -> List[Dict]:
    """
    Translates the 'text' field of each segment from English to Russian.

    :param segments: A list of dictionaries, where each dict has a 'text' key.
    :param model_path: Path to the local HF model.
    :param prompts_path: Path to the prompts.
    :param video_theme: Theme of the video.
    :param logger_name: Name of the logger.
    :return: The same list of dictionaries with 'text' translated.
    """
    logger = logging.getLogger(logger_name)

    logger.info(f"Loading translation model {str(model_path)}")
    model = Llama(
        model_path=str(model_path.absolute()),
        n_gpu_layers=-1,
        n_ctx=8192,
        verbose=False
    )
    logger.info(f"Translation model {model_path} was loaded")

    sys_prompt_t = (prompts_path / Path("translator_system")).read_text(encoding="utf-8")
    sys_prompt = get_prompt(sys_prompt_t, video_theme=video_theme)
    user_prompt_t = (prompts_path / Path("translator_user")).read_text(encoding="utf-8")

    context_size = 3

    phrases = [{f"segment{i}":
                    {"text": segment["text"],
                     "max_chars": max(math.ceil((segment["end"] - segment["start"]) * 15), len(segment["text"]))}}
               for i, segment in enumerate(segments)]

    results = []
    for batch_n, i in enumerate(range(0, len(phrases), context_size)):
        logger.info(f"Started translation batch {batch_n}/{len(phrases) // context_size + 1}")
        if i - context_size < 0:
            prev_context = None
        else:
            prev_context = phrases[i - context_size:i]
        if i + 2 * context_size > len(segments):
            future_context = None
        else:
            future_context = phrases[i + context_size:i + 2 * context_size]
        to_translate = phrases[i:i + context_size]
        user_prompt = make_user_prompt(user_prompt_t, to_translate, prev_context, future_context)

        fields = {f"segment{i + idx}": (SegmentTranslation, ...) for idx in range(len(to_translate))}
        dynamic_batch_model = create_model('DynamicBatchModel', **fields)
        schema = dynamic_batch_model.model_json_schema()

        messages = [
            {
                "role": "system",
                "content": sys_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        max_retries = 2
        delay_ms = 10
        for retry in range(1, max_retries + 1):
            try:
                json_string = generate(model, messages, schema)
                results += parse_result(json_string, to_translate, segments[i:i + context_size], logger)
            except Exception as e:
                logger.warning(f"Translate segment attempt {retry}/{max_retries} failed: {str(e)}")
                if retry == max_retries:
                    raise
                time.sleep(delay_ms / 1000)

    return results
