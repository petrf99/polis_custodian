import os
import httpx
from application.tech_utils.escape_md import escape_md
from logging import getLogger

logger = getLogger(__name__)

PARSE_MODE = "MarkdownV2"

async def send_http(url, payload, files=None):
    async with httpx.AsyncClient() as client:
        try:
            if files:
                response = await client.post(url, data=payload, files=files)
            else:
                response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.debug(f"[send_http] Returning: {type(response)} from {url}")
            # return await response.json()
            return response.json()
        except httpx.RequestError as e:
            logger.info(f"[NOTIFICATION_CENTER: TG API ERROR] {e}")
            return None


async def send_message(text, archetype, chat_id):
    TELEGRAM_BOT_TOKEN = os.getenv(f"{archetype.upper()}_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": escape_md(text),
        "parse_mode": PARSE_MODE
    }

    response = await send_http(url, payload)
    logger.debug(f"[send_message] got: {response} ({type(response)})")
    return 0 if response and response.get("ok") else -1


async def send_message_with_buttons(text, keyboard_dict, archetype, chat_id):
    TELEGRAM_BOT_TOKEN = os.getenv(f"{archetype.upper()}_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    keyboard = {
        "inline_keyboard": [
            [{"text": button, "callback_data": callback}]
            for button, callback in keyboard_dict.items()
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": escape_md(text),
        "reply_markup": keyboard,
        "parse_mode": PARSE_MODE
    }

    response = await send_http(url, payload)
    logger.debug(f"[send_message] got: {response} ({type(response)})")

    return 0 if response and response.get("ok") else -1


async def send_document(file_path, archetype, chat_id, caption=None):
    TELEGRAM_BOT_TOKEN = os.getenv(f"{archetype.upper()}_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

    with open(file_path, "rb") as file:
        files = {"document": (os.path.basename(file_path), file)}
        payload = {
            "chat_id": chat_id,
            "parse_mode": "MarkdownV2"
        }
        if caption:
            payload["caption"] = escape_md(caption)

        response = await send_http(url, payload, files=files)
        logger.debug(f"[send_message] got: {response} ({type(response)})")
        return 0 if response and response.get("ok") else -1
