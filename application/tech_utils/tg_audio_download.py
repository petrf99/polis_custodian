import os
import httpx
from logging import getLogger

logger = getLogger(__name__)

async def download_audio_from_telegram(file_id: str, save_path: str, archetype: str) -> str:
    TELEGRAM_BOT_TOKEN = os.getenv(f"{archetype.upper()}_BOT_TOKEN")

    async with httpx.AsyncClient() as client:
        file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        resp = await client.get(file_info_url)
        resp.raise_for_status()
        file_info = resp.json()
        file_path = file_info["result"]["file_path"]

        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_resp = await client.get(file_url)
        file_resp.raise_for_status()

        destination = os.path.join(save_path, f"{file_id}.ogg")
        with open(destination, "wb") as f:
            f.write(file_resp.content)

    logger.debug(f"[download_audio_from_telegram] Saved to: {destination}")
    return destination