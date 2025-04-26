import uuid
import logging
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from front.msg_params_get import extract_text_and_config
import datetime


from application.tech_utils.escape_md import escape_md


from application.custodian_archetypes.sage.back.task_manager import sg_tm, SageTask

from application.tech_utils.ngrok_set_up import get_public_url

NGROK_URL = get_public_url(8444)
if not NGROK_URL:
    raise RuntimeError("Ngrok is not running or not reachable")

# === Bot settings ===
BOT_TOKEN = os.getenv("SAGE_BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = NGROK_URL + WEBHOOK_PATH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", 600))

# === Response style ===
ACKNOWLEDGEMENTS = [
    "The Sage heard your question.",
    "Your words have reached the Sage.",
    "Your message echoes quietly in the temple.",
]

WAITING = [
    "A reply may come in time. Please be patient.",
    "The Sage is thinking. Or maybe not.",
    "No promise of an answer, but the question is now with the Sage.",
]

def sage_reply():
    return random.choice(ACKNOWLEDGEMENTS) + "\n" + random.choice(WAITING)

# === FSM setup ===
class SageStates(StatesGroup):
    waiting_for_reply = State()

# === Logging setup ===
logger = logging.getLogger(__name__)

# === Set up ===
import json

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Welcome to the Polis Sage Bot 🏛️\n\nSend text message if you want to speak with the Sage 👤\n\n☝🏻 You can specify some parameters by adding smth like this to the end of your question:"
    )
    config_str = json.dumps({'use_cache': True, 'search_width': 3, 'search_depth': 5, 'verbose': False})
    escaped = escape_md(config_str)

    await bot.send_message(
        message.chat.id,
        f"`{escaped}`",
        parse_mode="MarkdownV2"
    )
    #await bot.send_message(message.chat.id, f"`{escape_md("{'use_cache': true, 'search_width': 3, 'search_depth': 17}")}`, parse_mode="MarkdownV2")
    logger.info('[SAGE BOT IS WORKING]')



@dp.message(Command(commands=["reset", "stop", "restart"]))
async def reset_session(message: types.Message, command: CommandObject, state: FSMContext):
    data = await state.get_data()
    try:
        status_info = await sg_tm.get_status(data['question_id'])
        if status_info in ("PENDING", "STARTED"):
            await message.reply("❌ You can't terminate thinking process.")
            return
        elif status_info in ("SUCCESS"):
            await message.reply("❌ You already have your answer")
            return
    except Exception as e:
        logger.exception(f"[STATUS CHECK ERROR] {e}")
        await message.reply("Error while checking status...")
    await state.clear()
    chat_id = message.chat.id
    await bot.send_message(chat_id=chat_id, text="Thinking process terminated 🫡. You can ask another question.")


# === Check status command ===
@dp.message(Command(commands=["status"]))
async def check_status(message: types.Message, command: CommandObject):
    question_id = command.args

    if not question_id:
        await message.reply("❗ Please provide ID.\nUsage: /status `<id>`")
        return

    question_id = question_id.strip()

    try:
        status_info = await sg_tm.get_status(question_id)
    except Exception as e:
        logger.exception(f"[STATUS CHECK ERROR] {e}")
        await message.reply("❌ Error while checking status.")
        return

    task_status = status_info.get("status")

    if task_status in ("PENDING", "STARTED"):
        await message.reply(
            f"⏳ The Sage is still thinking about the question `{escape_md(question_id)}`\. Please wait\.",
            parse_mode="MarkdownV2"
        )
    elif task_status == "SUCCESS":
        await message.reply(
            f"✅ Question `{escape_md(question_id)}` has been answered\!",
            parse_mode="MarkdownV2"
        )
    elif task_status == "FAILURE":
        await message.reply(
            f"❌ Question `{escape_md(question_id)}` failed to answer\. Please try again or reduce the size of the file\.",
            parse_mode="MarkdownV2"
        )
    else:
        await message.reply(
            f"⚠️ No question found with ID `{escape_md(question_id)}`\. Have you sent a correct ID\?",
            parse_mode="MarkdownV2"
        )

# === Handlers ===

DEFAULT_CONFIG = {
    "use_cache": os.getenv("SAGE_USE_CACHE", "True").lower() == "true",
    "search_width": int(os.getenv("SAGE_SEARCH_WIDTH", 3)),
    "search_depth": int(os.getenv("SAGE_SEARCH_DEPTH", 5)),
    "verbose": os.getenv("SAGE_VERBOSE_MODE", "True").lower() == "true"
}

@dp.message(F.text)
async def handle_message(message: Message, state: FSMContext):
    chat_id = message.chat.id
    raw_text = message.text.strip()
    question_id = str(uuid.uuid4())

    # Проверка: уже есть незавершённый вопрос
    current_state = await state.get_state()
    if current_state == SageStates.waiting_for_reply.state:
        await message.answer("Don’t hurry. Your previous question must be dealt with first ✍🏻")
        return

    # Извлекаем текст и конфиг (пользовательский)
    question, user_config = extract_text_and_config(raw_text)

    # Объединяем пользовательский конфиг с дефолтами
    config = {**DEFAULT_CONFIG, **user_config}

    # Устанавливаем состояние ожидания
    await state.set_state(SageStates.waiting_for_reply)

    # Готовим данные
    data = {
        'question_dttm': datetime.datetime.now().isoformat(),
        'chat_id': chat_id,
        'question': question,
        'question_id': question_id,
        'use_cache': config['use_cache'],
        'search_width': config['search_width'],
        'search_depth': config['search_depth'],
        'verbose': config['verbose']
    }

    # Сохраняем в FSM
    await state.update_data(**data)
    logger.info(f"[SAGE] Received message from {chat_id}: {question}")
    await message.answer(sage_reply())

    try:
        await sg_tm.create_task(SageTask(data, 'sage_answer', None))
        logger.info(f"[SAGE] Task {question_id} scheduled for user {chat_id}")
        await bot.send_message(chat_id, text=f"Your question ID: `{escape_md(question_id)}`", parse_mode="MarkdownV2")
        await bot.send_message(chat_id, "You can check out its status with /status <ID> command 🙌🏻")
    except Exception as e:
        await state.clear()  # если ошибка — сбрасываем ожидание
        logger.exception(f"[SAGE] Failed to schedule task for {chat_id}: {e}")
        await message.answer("Something went wrong. The Sage stays silent for now 😴")


@dp.callback_query(SageStates.waiting_for_reply, F.data.startswith("feedback_"))
async def sage_feedback(callback: types.CallbackQuery, state: FSMContext):
    rate = callback.data.split('_')[1]
    data = await state.get_data()
    sg_tm.save_feedback(data['question_id'], rate)

    await state.clear()

    await callback.message.answer("Thank you. Now you can ask the Sage another question 🌤\n\n☝🏻 You can specify some parameters by adding smth like this to the end of your question:")
    config_str = json.dumps({'use_cache': True, 'search_width': 3, 'search_depth': 5, 'verbose': False})
    escaped = escape_md(config_str)

    await bot.send_message(
        callback.message.chat.id,
        f"`{escaped}`",
        parse_mode="MarkdownV2"
    )


# Set up web server
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook set up: {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    logger.error("❌ Webhook deleted")

app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Привязка webhook пути
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

def start_bot():
    web.run_app(app, host="0.0.0.0", port=8444)

if __name__ == "__main__":
    start_bot()
