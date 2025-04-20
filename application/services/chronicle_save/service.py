from worker import run_import
from aiogram import Bot

from logging import getLogger
logger = getLogger(__name__)

async def save_to_chronicle(bot: Bot, chat_id, session_id):
    logger.info(f'[CHRONICLE UPLOAD STARTED] {session_id}')
    ut_file_name = f"jobs/speech2text/temp/utterances_{session_id}.json"

    await bot.send_message(
        chat_id=chat_id,
        text=f"⚙️ Your dialog is being uploaded to the Chronicle.\nID: {session_id}\n\nYou will be notified once the upload is done. 🔔"
    )

    run_import(ut_file_name)

    await bot.send_message(
        chat_id=chat_id,
        text=f"👌 Your file was uploaded to the Chronicle.\nID: {session_id}"
    )

    import os

    os.remove(ut_file_name)

    logger.info(f"[CHRONICLE UPLOAD ENDED] {session_id}")