import os
import json
import uuid
import whisper
from math import exp
from pathlib import Path

import torch
torch.set_num_threads(int(os.getenv("TRANSCRIBE_THREADS", 2)))

from logging import getLogger
logger = getLogger(__name__)

from application.tech_utils.safe_func_run import safe_run_sync
@safe_run_sync
def transcribe_audio(file_path: str, args: dict) -> list:
    """
    Transcribes an audio file using Whisper and returns:
    [info_summary, transcript_file_path or None]
    """
    model_size = args.get("model", "small")
    language = args.get("language", None)
    temperature = args.get("temperature") or 0.0
    session_id = args.get("session_id", str(uuid.uuid4()))
    user_id = args.get("user_id", '')
    session_start_dttm = args.get("session_start_dttm", '')
    output_type = args.get("output_type", "text")

    BASE_DIR = Path.cwd().parent.parent #Path(__file__).resolve().parent.parent
    text_save_dir = BASE_DIR / os.getenv("TRANSCRIPTS_DIR", "temp_data/transcripts")
    json_save_dir = BASE_DIR / os.getenv("SEGMENTS_JSON_DIR", "temp_data/segments_json")
    os.makedirs(text_save_dir, exist_ok=True)
    os.makedirs(json_save_dir, exist_ok=True)

    logger.info(f"[TRANSCRIBE] Starting transcription {session_id}\nModel={model_size}, lang={language}, temp={temperature}")

    # Load whisper model (this can be cached at higher level too)
    logger.info("[LOAD MODEL]")
    model = whisper.load_model(model_size)

    # Transcribe audio
    logger.info("[EXECUTE WHISPER]")
    result = model.transcribe(
        file_path,
        language=None if language == "auto" else language,
        temperature=temperature
    )
    logger.info("[WHISPER EXECUTED]")

    segments = result["segments"]

    utterances = []

    for seg in segments:
        utterance = {
            "id": str(uuid.uuid4()),
            "dialog_id": str(session_id),
            "content": seg["text"],
            "start_time": seg["start"],
            "end_time": seg["end"],
            "segment_number": seg["id"],
            "created_at": str(session_start_dttm),
            "speaker": user_id,         # Можно будет потом добавить
            "metadata": {}
        }
        utterances.append(utterance)

    with open(os.path.join(json_save_dir, f"utterances_{session_id}.json"), "w", encoding="utf-8") as f:
        json.dump(utterances, f, ensure_ascii=False, indent=2)


    avg_logprob = result["segments"][0]["avg_logprob"] if result.get("segments") else None
    no_speech_prob = result.get("no_speech_prob", None)

    summary = (
        f"Language: {result.get('language')}\n"
        f"Model size: {model_size}\n"
        f"Temperature: {temperature}\n"
        f"Degree of confidence: {round(exp(avg_logprob) * 100, 2)}%\n"
        f"No-speech file probability: {str(round(no_speech_prob * 100, 2)) + '%' if no_speech_prob is not None else 'None'}\n"
    )

    # Decide whether to save full text
    file_path_txt = None
    if output_type == "text" and result["text"].strip():
        transcript = "\n\n".join(u["content"].strip() for u in utterances)
        filename = f"transcript_{user_id}_{session_start_dttm}.txt"
        file_path_txt = os.path.join(text_save_dir, filename)
        with open(file_path_txt, "w", encoding="utf-8") as f:
            f.write(transcript)

    logger.info("[WHISPER WORKER SUCCESSFULLY FINISHED]")

    return [summary, file_path_txt, session_id]