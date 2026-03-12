import logging
from .TranslationModel import TranslationModel
from .FormattingModel import FormattingModel
from typing import List, Dict, Any
from pathlib import Path
import math
import json
from pydantic import BaseModel
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


def count_max_chars(orig_text: str, start: float, end: float) -> int:
    return max(len(orig_text), 15 * math.ceil((end - start)))


def translate_segments(segments: List[Dict[str, Any]], model_path: Path,
                       logger_name: str) -> List[Dict[str, Any]]:
    logger = logging.getLogger(logger_name)

    logger.info(f"Loading translation model {str(model_path)}")
    model = TranslationModel(str(model_path.absolute()), logger_name)
    logger.info(f"Translation model {str(model_path)} was loaded")

    logger.info(f"Starting translation of {len(segments)} segments")
    translated_segs = []
    for i, segment in enumerate(segments):
        translated_segs.append({"start": segment["start"],
                                "end": segment["end"],
                                "original": segment["text"]})

        text = segment["text"]
        output = model.generate_output(text)

        translated_segs[-1]["translated"] = output

        if i % 10 == 0 or i == len(segments):
            logger.info(f"Translated {i}/{len(segments)} segments")

    return translated_segs


def format_segments(segments: List[Dict[str, Any]], model_path: Path, prompts_path: Path, video_theme: str,
                    logger_name: str) -> List[Dict[str, Any]]:
    logger = logging.getLogger(logger_name)

    logger.info(f"Loading formatting model {str(model_path)}")
    # model = FormattingModel(str(model_path.absolute()), logger_name)
    logger.info(f"Formatting model {str(model_path)} was loaded")

    sys_prompt_t = (prompts_path / "formatter_system").read_text(encoding="utf-8")
    sys_prompt = get_prompt(sys_prompt_t, video_theme=video_theme)
    user_prompt_t = (prompts_path / "formatter_user").read_text(encoding="utf-8")

    batch_size = 8
    inter_size = 4
    logger.info(f"Starting formatting of {len(segments)} segments")
    cur_idx = 0
    batch = segments[cur_idx:batch_size]
    while len(batch) > 0:
        user_load = [{"phrase_id": i,
                      "original": seg["original"],
                      "translated": seg["translated"],
                      "max_chars": count_max_chars(seg["original"], seg["start"], seg["end"])}
                     for i, seg in enumerate(batch)]
        user_prompt = get_prompt(user_prompt_t, user_load=json.dumps(user_load, ensure_ascii=False, indent=2))

        model = FormattingModel(str(model_path.absolute()), logger_name)
        output = model.generate_output(sys_prompt, user_prompt)

        for dct in output:
            idx = dct["phrase_id"]
            batch[idx]["translated"] = dct["translated"]


        if cur_idx + batch_size >= len(segments):
            break
        cur_idx = cur_idx + batch_size - inter_size
        if cur_idx + batch_size > len(segments):
            cur_idx = len(segments) - batch_size
        batch = segments[cur_idx:cur_idx + batch_size]

        logger.info(f"Formatted {cur_idx}/{len(segments)} segments")

    return segments


def translate_pipeline(segments: List[Dict], translator_model_path: Path, formatter_model_path: Path,
                       prompts_path: Path, video_theme: str,
                       logger_name: str) -> List[Dict]:
    """
    Translates the 'text' field of each segment from English to Russian.

    :param segments: A list of dictionaries, where each dict has a 'text' key.
    :param translator_model_path: Path to the local translator model.
    :param formatter_model_path: Path to the local formatter model.
    :param prompts_path: Path to the prompts.
    :param video_theme: Theme of the video.
    :param logger_name: Name of the logger.
    :return: The same list of dictionaries with 'text' translated.
    """
    logger = logging.getLogger(logger_name)

    #translated_segments = translate_segments(segments, translator_model_path, logger_name)
    #Path(r"A:\Progs\PyCharmProjects\VideoEnToRu\backend\app\Translation\temp\translated.json").write_text(
    #    json.dumps(translated_segments, ensure_ascii=False, indent=2))
    with open(r"A:\Progs\PyCharmProjects\VideoEnToRu\backend\app\Translation\temp\translated.json", 'r') as f:
        translated_segments = json.load(f, strict=False)
    result = format_segments(translated_segments, formatter_model_path, prompts_path, video_theme, logger_name)
    Path(r"A:\Progs\PyCharmProjects\VideoEnToRu\backend\app\Translation\temp\formatted.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2))
    return result
