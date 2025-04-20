from application.services.chronicle_save.worker import run_import
from aiogram import Bot
from pathlib import Path
import os

from logging import getLogger
logger = getLogger(__name__)

async def save_to_chronicle(bot: Bot, data):
    chat_id = data['chat_id']
    session_id = data['session_id']
    dialog_name = data['dialog_name']
    topic_id = data['topic_id']
    source = data['source']
    logger.info(f'[CHRONICLE UPLOAD STARTED] {session_id}')

    BASE_DIR = Path.cwd().parent.parent #Path(__file__).resolve().parent.parent
    json_save_dir = BASE_DIR / os.getenv("SEGMENTS_JSON_DIR", "temp_data/segments_json")

    ut_file_name = os.path.join(json_save_dir, f"utterances_{session_id}.json")

    await bot.send_message(
        chat_id=chat_id,
        text=f"⚙️ Your dialog is being uploaded to the Chronicle.\nID: {session_id}\n\nYou will be notified once the upload is done. 🔔"
    )

    run_import(ut_file_name, dialog_name, topic_id, source)

    await bot.send_message(
        chat_id=chat_id,
        text=f"👌 Your file was uploaded to the Chronicle.\nID: {session_id}"
    )

    os.remove(ut_file_name)

    logger.info(f"[CHRONICLE UPLOAD ENDED] {session_id}")