import os
import json
import uuid
from pathlib import Path

from faster_whisper import WhisperModel

from logging import getLogger
logger = getLogger(__name__)

from application.tech_utils.safe_func_run import safe_run_sync

@safe_run_sync
def transcribe_audio(file_path: str, args: dict) -> list:
    """
    Transcribes an audio file using faster-whisper and returns:
    [info_summary, transcript_file_path or None]
    """
    model_size = args.get("model", "small")
    language = args.get("language", None)
    session_id = args.get("session_id", str(uuid.uuid4()))
    user_id = args.get("user_id", "")
    session_start_dttm = args.get("session_start_dttm", '')
    output_type = args.get("output_type", "text")

    BASE_DIR = Path.cwd().parent.parent
    text_save_dir = BASE_DIR / os.getenv("TRANSCRIPTS_DIR", "temp_data/transcripts")
    json_save_dir = BASE_DIR / os.getenv("SEGMENTS_JSON_DIR", "temp_data/segments_json")
    os.makedirs(text_save_dir, exist_ok=True)
    os.makedirs(json_save_dir, exist_ok=True)

    logger.info(f"[TRANSCRIBE] Starting transcription {session_id}\nModel={model_size}, lang={language}")
    logger.info("[LOAD MODEL]")

    # Initialize faster-whisper model
    beam_size = int(os.getenv("FASTER_WHISPER_BEAM_SIZE", 5))
    compute_type = os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "int8")
    device = os.getenv("FASTER_WHISPER_DEVICE", "cpu")
    cpu_threads = int(os.getenv("TRANSCRIBE_THREADS", 2))
    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        cpu_threads=cpu_threads
    )

    logger.info("[EXECUTING FASTER-WHISPER]")

    segments, info = model.transcribe(
        file_path,
        language=None if language == "auto" else language,
        beam_size=beam_size,
        vad_filter=True  # optional silence filtering
    )

    logger.info("[FASTER-WHISPER EXECUTED]")

    if bool(os.getenv("SEGMENT_AUDIO_AS_TEXT")):
        full_text = " ".join([seg.text.strip() for seg in segments])

        not_empty_text_flg = False
        if full_text.strip():
            not_empty_text_flg = True

            filename = f"transcript_{session_id}.txt"
            file_path_txt = os.path.join(text_save_dir, filename)
            with open(file_path_txt, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            from application.services.text_processing.worker import segment_text_file

            summary = segment_text_file(file_path_txt, {'session_id':session_id,
                                            'user_id':user_id,
                                            'session_start_dttm':session_start_dttm})[0]
            os.remove(file_path_txt)

    else:
        utterances = []
        for idx, seg in enumerate(segments):
            utterance = {
                "id": str(uuid.uuid4()),
                "dialog_id": str(session_id),
                "content": seg.text.strip(),
                "start_time": seg.start,
                "end_time": seg.end,
                "segment_number": idx,
                "created_at": str(session_start_dttm),
                "speaker": user_id,
                "metadata": {}
            }
            utterances.append(utterance)

        with open(os.path.join(json_save_dir, f"utterances_{session_id}.json"), "w", encoding="utf-8") as f:
            json.dump(utterances, f, ensure_ascii=False, indent=2)

        if utterances:
            not_empty_text_flg = True

        summary = (
            f"Language: {info.language}\n"
            f"Model size: {model_size}\n"
            f"Duration: {round(info.duration, 2)}s\n"
            f"Segments: {len(utterances)}\n"
        )

    with open(os.path.join(json_save_dir, f"utterances_{session_id}.json"), "r", encoding="utf-8") as f:
        utterances = json.load(f)

    file_path_txt = None
    if output_type == "text" and not_empty_text_flg:
        transcript = "\n\n".join(u["content"].strip() for u in utterances)
        filename = f"transcript_{session_id}.txt"
        file_path_txt = os.path.join(text_save_dir, filename)
        with open(file_path_txt, "w", encoding="utf-8") as f:
            f.write(transcript)

    logger.info("[FASTER-WHISPER WORKER SUCCESSFULLY FINISHED]")

    return [summary, file_path_txt, session_id]