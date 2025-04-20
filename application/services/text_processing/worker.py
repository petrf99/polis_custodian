import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from logging import getLogger

import tiktoken
tokenizer = tiktoken.get_encoding("cl100k_base")  # совместим с GPT-4, ChatGPT

logger = getLogger(__name__)

# Один раз загрузим токенизаторы
import nltk
# 1. Указываем, куда скачивать (и где потом искать)
nltk.data.path.append("/app/nltk_data")
# 2. Скачиваем в это место
nltk.download("punkt", download_dir="/app/nltk_data")
nltk.download("punkt_tab", download_dir="/app/nltk_data")


from application.tech_utils.safe_func_run import safe_run_sync

@safe_run_sync
def segment_text_file(file_path: str, args: dict):
    logger.info("[TEXT SEGMENTATION JOB RUN]")
    session_id = args.get("session_id", str(uuid.uuid4()))
    user_id = args.get("user_id", "")
    session_start_dttm = args.get("session_start_dttm", datetime.now().isoformat())

    BASE_DIR = Path.cwd().parent.parent
    text_save_dir = BASE_DIR / os.getenv("TRANSCRIPTS_DIR", "temp_data/transcripts")
    json_save_dir = BASE_DIR / os.getenv("SEGMENTS_JSON_DIR", "temp_data/segments_json")
    os.makedirs(text_save_dir, exist_ok=True)
    os.makedirs(json_save_dir, exist_ok=True)

    max_words = int(os.getenv("MAX_TEXT_WORDS_PER_TEXT_SEGMENT", "50"))
    min_words = int(os.getenv("MIN_WORDS_PER_TEXT_SEGMENT", "10"))
    merge_short = bool(os.getenv("TEXT_SEGMENT_MERGE_SHORT", True))
    strategy = os.getenv("TEXT_SEGMENT_STRATEGY", "sentence")

    logger.info("[TEXT SEGMENTATION STARTED]")
    # Чтение текста
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Делим на фрагменты
    if strategy == "paragraph":
        raw_segments = [p.strip() for p in text.split("\n\n") if p.strip()]
    elif strategy == 'sentence':  
        from nltk.tokenize import sent_tokenize
        raw_segments = sent_tokenize(text)
    elif strategy == "token":
        tokens = tokenizer.encode(text)
        max_tokens = int(args.get("max_tokens_per_segment", 100))

        # Разбиваем токены на чанки
        raw_segments = []
        for i in range(0, len(tokens), max_tokens):
            chunk = tokens[i:i + max_tokens]
            chunk_text = tokenizer.decode(chunk)
            raw_segments.append(chunk_text)

    else:
        raise ValueError(f"Unknown segmentation strategy: {strategy}")
    

    # Разбиваем и объединяем при необходимости
    segments = []
    buffer = ""
    for seg in raw_segments:
        words = seg.split()
        if len(words) >= min_words and len(words) <= max_words:
            segments.append(seg)
        elif len(words) > max_words:
            # Разбиваем длинный сегмент на чанки
            for i in range(0, len(words), max_words):
                chunk = " ".join(words[i:i+max_words])
                segments.append(chunk)
        elif merge_short:
            buffer += " " + seg
            if len(buffer.split()) >= min_words:
                segments.append(buffer.strip())
                buffer = ""
        else:
            continue

    if buffer:
        segments.append(buffer.strip())

    # Сохраняем сегменты в json в формате Whisper
    utterances = []
    for idx, seg in enumerate(segments):
        utterances.append({
            "id": str(uuid.uuid4()),
            "dialog_id": session_id,
            "content": seg,
            "start_time": 0.0,
            "end_time": 0.0,
            "segment_number": idx,
            "created_at": session_start_dttm,
            "speaker": user_id,
            "metadata": {}
        })

    with open(os.path.join(json_save_dir, f"utterances_{session_id}.json"), "w", encoding="utf-8") as f:
        json.dump(utterances, f, ensure_ascii=False, indent=2)

    summary = (
        f"Segments: {len(utterances)}\n"
        f"Total words: {len(text.split())}\n"
        f"Segment strategy: {strategy}\n"
        f"Max words per segment: {max_words}\n"
    )

    logger.info("[TEXT SEGMENTATION COMPLETED]")
    return [summary, 
            None, # "No transcript file path for texts so far"
            session_id]
