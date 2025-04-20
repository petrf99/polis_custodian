import os
import httpx

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def send_message_async(chat_id: int, text: str):
    import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def send_message_with_buttons(chat_id, session_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Yes, save it",
                    "callback_data": f"store_yes_{chat_id}_{session_id}"
                },
                {
                    "text": "No, don't save",
                    "callback_data": f"store_no_{chat_id}_{session_id}"
                }
            ]
        ]
    }

    payload = {
        "chat_id": chat_id,
        "text": "Do you want to save it to our Chronicle? 📜",
        "reply_markup": keyboard
    }


    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"[TG API ERROR] {e}")
            return None




import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_message_via_api(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[TG API ERROR] {e}")
        return None
