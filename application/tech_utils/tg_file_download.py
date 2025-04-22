import os
import httpx
import aiofiles
from uuid import uuid4
from logging import getLogger
import cgi
import re

logger = getLogger(__name__)

from urllib.parse import urlparse

def to_tmpfiles_download_url(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/", 1)

    if len(parts) < 2:
        raise ValueError("Invalid tmpfiles.org URL format")

    file_id, filename = parts
    return f"https://tmpfiles.org/dl/{file_id}/{filename}"



async def download_file_from_telegram(file_id: str, save_path: str, archetype: str, file_type: str) -> str:
    TELEGRAM_BOT_TOKEN = os.getenv(f"{archetype.upper()}_BOT_TOKEN")

    async with httpx.AsyncClient() as client:
        # === file.io mode ===
        if file_type == "file_io_link":
            if "tmpfiles.org" in file_id:
                file_id = to_tmpfiles_download_url(file_id)
            logger.info(f"[download] file.io mode: {file_id}")
            response = await client.get(file_id)
            response.raise_for_status()

            if 'text/html' in response.headers.get("Content-Type", ""):
                raise ValueError(f"Got HTML page instead of audio file for URL: {file_id}")

            cd = response.headers.get("Content-Disposition")
            filename = f"{uuid4().hex}.bin"

            if cd:
                _, params = cgi.parse_header(cd)
                filename = params.get("filename", filename)

            full_path = os.path.join(save_path, filename)
            async with aiofiles.open(full_path, 'wb') as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)
            
            logger.info(f'[DOWNLOADED FILE FROM LIMEWARE] {full_path}')

            return full_path

        # === Telegram file mode ===
        file_info_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        resp = await client.get(file_info_url)
        resp.raise_for_status()
        file_info = resp.json()
        file_path = file_info["result"]["file_path"]

        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        file_resp = await client.get(file_url)
        file_resp.raise_for_status()

        filename = os.path.basename(file_path)
        destination = os.path.join(save_path, filename)

        async with aiofiles.open(destination, "wb") as f:
            await f.write(file_resp.content)

        logger.info(f"[download_file_from_telegram] Saved to: {destination}")
        return destination
