# services/transcript.py
from pathlib import Path
import os
import asyncio
import datetime
from application.services.transcribe_audio.worker import transcribe_audio
from application.services.transcribe_audio.scripts.transcript_duration_estimate import estimate_transcription_time
from application.tech_utils.tg_file_download import download_file_from_telegram
from application.tech_utils.notification_center import send_message, send_message_with_buttons, send_document

BASE_DIR = Path.cwd().parent.parent
audio_save_dir = BASE_DIR / os.getenv("AUDIO_DIR", "temp_data/audio")
os.makedirs(audio_save_dir, exist_ok=True)

from logging import getLogger
logger = getLogger(__name__)

async def run_transcription(data: dict):
    session_id = data['session_id']
    chat_id = data['chat_id']
    logger.info(f"[TRANSCRIPT STARTED. DOWNLOAD AUDIO FROM TG] {session_id}")
    logger.info(f"[TG-DL] Trying to download: {data['file_id']}")
    file_path = await download_file_from_telegram(data['file_id'], 
                                                  audio_save_dir, 'CHRONICLER', 
                                                  file_type=data.get("file_type", "telegram"))
    transcript_dur = estimate_transcription_time(file_path, data['model'])

    await send_message(f"⏳ Estimated time for transcript:\n\n{str(datetime.timedelta(seconds=transcript_dur))}",
                       'CHRONICLER', chat_id)

    logger.info("[START WHISPER JOB]")
    result = await asyncio.to_thread(transcribe_audio, file_path, data)
    logger.info("[WHISPER JOB ENDED]")

    await send_message(f"✅ Done! Here is some info about your transcript 👇\nID: {(session_id)}\n\n{result[0]}",
                       'CHRONICLER', chat_id)

    if result[1] is not None:
        await send_document(result[1], 'CHRONICLER', chat_id, f"Your transcript, Sir 📄\nID: {session_id}")


    await send_message_with_buttons(f"Do you want to save it to our Chronicle? 📜", 
                              {'Yes, save it':f"store_yes_{data['chat_id']}_{data['session_id']}_audio",
                               "No, don't save":f"store_no_{data['chat_id']}_{data['session_id']}_audio"}, 
                               'CHRONICLER', chat_id)

    if result[1] is not None:
        os.remove(result[1])
    os.remove(file_path)

    logger.info(f"[TRANSCRIPT ENDED] {session_id}")