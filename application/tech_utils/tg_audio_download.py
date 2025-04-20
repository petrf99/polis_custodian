import os
from aiogram import Bot

# Download audio from Telegram
async def download_audio_from_telegram(bot: Bot, file_id: str, save_path: str) -> str:
    file = await bot.get_file(file_id)
    file_path = file.file_path
    destination = os.path.join(save_path, f"{file_id}.ogg")

    await bot.download_file(file_path, destination)
    return destination

