# services/transcript.py
from pathlib import Path
import os
import asyncio
from application.tech_utils.escape_md import escape_md
from application.services.text_processing.worker import segment_text_file
from application.tech_utils.tg_file_download import download_file_from_telegram
from application.tech_utils.notification_center import send_message, send_message_with_buttons, send_document

BASE_DIR = Path.cwd().parent.parent
text_save_dir = BASE_DIR / os.getenv("TEXT_DIR", "temp_data/text")
os.makedirs(text_save_dir, exist_ok=True)

from logging import getLogger
logger = getLogger(__name__)

async def process_text_service(data: dict):
    session_id = data['session_id']
    chat_id = data['chat_id']
    if data['file_type'] == 'text_file':
        logger.info(f"[DOWNLOAD TEXT FILE FROM TG] {session_id}")
        file_path = await download_file_from_telegram(data['file_id'], text_save_dir, 'CHRONICLER') 
    elif data['file_type'] == 'text_message':
        file_path = os.path.join(text_save_dir, f"text_{session_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data['raw_text'])

    logger.info(f"[TEXT PROCESSING STARTED] {session_id}")
    result = await asyncio.to_thread(segment_text_file, file_path, data)
    logger.info(f"[TEXT PROCESSING ENDED] {session_id}")

    await send_message(f"✅ Done! Here is some info about your text 👇\nID: {(session_id)}\n\n{result[0]}",
                       'CHRONICLER', chat_id)

    if result[1] is not None:
        await send_document(result[1], 'CHRONICLER', chat_id, f"Your processing result, Sir 📄\nID: {session_id}")


    await send_message_with_buttons(f"Do you want to save it to our Chronicle? 📜", 
                              {'Yes, save it':f"store_yes_{data['chat_id']}_{data['session_id']}_text",
                               "No, don't save":f"store_no_{data['chat_id']}_{data['session_id']}_text"}, 
                               'CHRONICLER', chat_id)

    if result[1] is not None:
        os.remove(result[1])
    os.remove(file_path)

    logger.info(f"[TRANSCRIPT ENDED] {session_id}")



    
    