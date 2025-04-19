# services/transcript.py
from aiogram import Bot, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pathlib import Path
import os
import asyncio
import datetime
from jobs.speech2text.whisper_worker import transcribe_audio
from services.transcript.transcript_duration_estimate import estimate_transcription_time
from services.ui_utils.tg_audio_download import download_audio_from_telegram

BASE_DIR = Path.cwd()
audio_save_dir = BASE_DIR / os.getenv("AUDIO_DIR", "temp_data/audio")
os.makedirs(audio_save_dir, exist_ok=True)

from logging import getLogger
logger = getLogger(__name__)

async def run_transcription(bot: Bot, data: dict):
    session_id = data['session_id']
    logger.info(f"[TRANSCRIPT STARTED. DOWNLOAD AUDIO FROM TG] {session_id}")
    file_path = await download_audio_from_telegram(bot, data["file_id"], save_path=audio_save_dir)
    transcript_dur = estimate_transcription_time(file_path, data['model'])

    await bot.send_message(
        chat_id=data['chat_id'],
        text=f"⏳ Estimated time for transcript:\n\n{str(datetime.timedelta(seconds=transcript_dur))}"
    )

    logger.info("[START WHISPER JOB]")
    result = await asyncio.to_thread(transcribe_audio, file_path, data)
    logger.info("[WHISPER JOB ENDED]")

    await bot.send_message(
        chat_id=data['chat_id'],
        text=f"✅ Done! Here is some info about your transcript 👇\nID: {session_id}\n\n{result[0]}"
    )

    if result[1] is not None:
        await bot.send_document(
            chat_id=data['chat_id'],
            document=types.FSInputFile(result[1]),
            caption=f"Your transcript, Sir 📄\nID: {session_id}"
        )

    # Store decision buttons
    store_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Yes, save it", callback_data=f"store_yes_{data['chat_id']}_{data['session_id']}"),
        InlineKeyboardButton(text="No, don't save", callback_data=f"store_no_{data['chat_id']}_{data['session_id']}")]
    ])

    await bot.send_message(
        chat_id=data['chat_id'],
        text=f"Do you want to save it to our Chronicle? 📜",
        reply_markup=store_kb
    )

    if result[1] is not None:
        os.remove(result[1])
    os.remove(file_path)

    logger.info(f"[TRANSCRIPT ENDED] {session_id}")