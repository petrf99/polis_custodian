from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
import datetime
import uuid
from application.tech_utils.escape_md import escape_md
from application.tech_utils.tg_sess_timeout_watcher import start_timeout_watcher
from front.create_buttons import create_buttons
from application.custodian_archetypes.chronicler.back.get_topics_list import get_topics_list
from application.custodian_archetypes.chronicler.back.task_manager import chr_tm, ChroniclerTask
import requests
import re
from logging import getLogger
logger = getLogger(__name__)

from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web


# FSM
class FormStates(StatesGroup):
    waiting_language = State()
    waiting_model = State()
    waiting_output_type = State()
    waiting_file = State()
    waiting_fileio_type = State()


# FSM: общий для Chronicle
class ChronicleFlow(StatesGroup):
    waiting_for_topic = State()
    waiting_for_dialog_name = State()


# Set up bot
def get_ngrok_url():
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = resp.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
    except Exception as e:
        print(f"❌ Не удалось получить ngrok URL: {e}")
        return None

NGROK_URL = get_ngrok_url()
if not NGROK_URL:
    raise RuntimeError("Ngrok is not running or not reachable")


BOT_TOKEN = os.getenv("CHRONICLER_BOT_TOKEN")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = NGROK_URL + WEBHOOK_PATH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", 600))

# Create buttons
start_kb, language_kb, model_kb, output_kb = create_buttons()

topics_list = None


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Welcome to the Polis Chronicler Bot 🏛️\nSend audio or text to transcribe or archive it.\nPress the button below to start:",
        reply_markup=start_kb
    )
    logger.info('[BOT IS WORKING]')

@dp.message(Command(commands=["reset", "stop", "restart"]))
async def reset_session(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    chat_id = message.chat.id
    await bot.send_message(chat_id=chat_id, text="Session terminated 🫡. Ready for another one:", reply_markup=start_kb)

@dp.message(Command(commands=["status"]))
async def check_status(message: types.Message, command: CommandObject):
    session_id = command.args

    if not session_id:
        await message.reply("❗ Please provide ID.\nUsage: /status `<id>`")
        return

    session_id = session_id.strip()

    try:
        status_info = await chr_tm.get_status(session_id)
    except Exception as e:
        logger.exception(f"[STATUS CHECK ERROR] {e}")
        await message.reply("❌ Error while checking status.")
        return

    task_status = status_info.get("status")

    if task_status in ("PENDING", "STARTED"):
        await message.reply(
            f"⏳ Task `{escape_md(session_id)}` is still in progress\. Please wait\.",
            parse_mode="MarkdownV2"
        )
    elif task_status == "SUCCESS":
        await message.reply(
            f"✅ Task `{escape_md(session_id)}` has been completed\!",
            parse_mode="MarkdownV2"
        )
    elif task_status == "FAILURE":
        await message.reply(
            f"❌ Task `{escape_md(session_id)}` failed to process\. Please try again or reduce the size of the file\.",
            parse_mode="MarkdownV2"
        )
    else:
        await message.reply(
            f"⚠️ No task found with ID `{escape_md(session_id)}`\. Have you sent a correct ID\?",
            parse_mode="MarkdownV2"
        )


@dp.callback_query(F.data == "start_session")
async def start_session(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await callback.answer("You already have an active session. Finish it first. 🔄", show_alert=True)
        return

    session_id = str(uuid.uuid4())
    logger.info(f"[START SESSION] {session_id}")

    await state.update_data(session_id=session_id)
    await state.update_data(session_start_dttm=datetime.datetime.now().isoformat())
    await state.update_data(user_id=callback.from_user.id)

    await callback.message.answer("📥 Please send an audio file / voice message or text (.txt or just type it)\n\n⚠️Note: max file size via Telegram - 20MB.\n\n☝🏻 If your file exceed this limit please upload it to https://tmpfiles.org and send the link to the chat.")
    await state.set_state(FormStates.waiting_file)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_file, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))



@dp.message(
    FormStates.waiting_file)
async def initial_file_handler(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    file = message.voice or message.audio or message.document

    MAX_SIZE = 20 * 1024 * 1024  # 20 MB

    file_size = (
            (message.document and message.document.file_size) or
            (message.voice and message.voice.file_size) or
            (message.audio and message.audio.file_size)
        )

    if file_size and file_size > MAX_SIZE:
        await message.answer("⚠️ File is too big... Max size — 20MB.\n\nPlease upload it to https://tmpfiles.org and send the link to the chat")
        await state.set_state(FormStates.waiting_file)

        asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_file, timeout_seconds=timeout_seconds, callback_message=message, start_kb=start_kb))
        return

    # AUDIO
    if file and (message.voice or message.audio or 
                (message.document and message.document.mime_type.startswith("audio/"))):

        await message.reply("🎧 Audio received. Let's configure transcription.")
        await state.update_data(file_id=file.file_id, file_type='audio', chat_id=chat_id)

        await message.answer("Choose the language of your audio:", reply_markup=language_kb)
        await state.set_state(FormStates.waiting_language)

        asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_language, timeout_seconds=timeout_seconds, callback_message=message, start_kb=start_kb))

        return

    # TEXT
    elif (message.document and message.document.mime_type == "text/plain") or message.text:

        FILE_IO_REGEX = r"https:\/\/tmpfiles\.org\/(?:dl\/)?[a-zA-Z0-9\/\-_\.]+"
        # === File share LINK ===
        if message.text and re.match(FILE_IO_REGEX, message.text.strip()):
            url = message.text.strip()
            file_io_type_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Text", callback_data="fileio_type_text")],
                [InlineKeyboardButton(text="🎧 Audio", callback_data="fileio_type_audio")]
            ])
            await message.reply("📁 Got the link. Please specify the type of the file.", reply_markup=file_io_type_kb)

            await state.update_data(file_id=url, file_type='file_io_link', chat_id=chat_id)

            await state.set_state(FormStates.waiting_fileio_type)

            asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_fileio_type, timeout_seconds=timeout_seconds, callback_message=message, start_kb=start_kb))
            return

        # === plain .txt file ===
        if message.document:
            await message.reply("📄 Text file received. It's being processed. Please wait.")
            await state.update_data(file_id=message.document.file_id, file_type='text_file', chat_id=chat_id)

        # === plain text ===
        else:
            await message.reply("📝 Text message received. It's being processed. Please wait.")
            await state.update_data(raw_text=message.text, file_type='text_message', chat_id=chat_id)

        data = await state.get_data()
        await bot.send_message(chat_id=data['chat_id'], text=f"Process ID: `{escape_md(data['session_id'])}`", parse_mode="MarkdownV2")

        logger.info(f"[SEND TEXT TASK] {data['session_id']}")
        await chr_tm.create_task(ChroniclerTask(data, 'text_processing', None))

        await state.clear()
        await bot.send_message(chat_id=data['chat_id'], text="Session ended 🫡. Ready for another one:", reply_markup=start_kb)
        return
    else:
        await message.reply("❌ Unsupported file type. Please send audio or plain text.")
        return


@dp.callback_query(FormStates.waiting_fileio_type, F.data.in_(["fileio_type_text", "fileio_type_audio"]))
async def handle_fileio_type(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_type = "text_processing" if callback.data == "fileio_type_text" else "transcribe_audio"

    if task_type == "text_processing":
        await bot.send_message(chat_id=data['chat_id'], text=f"Process ID: `{escape_md(data['session_id'])}`", parse_mode="MarkdownV2")

        logger.info(f"[SEND TEXT TASK] {data['session_id']}")
        await chr_tm.create_task(ChroniclerTask(data, task_type, None))

        await state.clear()
        await bot.send_message(chat_id=data['chat_id'], text="Session ended 🫡. Ready for another one:", reply_markup=start_kb)
        
        return
    else:
        await callback.message.answer("Choose the language of your audio:", reply_markup=language_kb)
        await state.set_state(FormStates.waiting_language)

        asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_language, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))

        return


@dp.callback_query(FormStates.waiting_language, F.data.startswith("lang_"))
async def select_language(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    await callback.message.answer("Choose the model size:", reply_markup=model_kb)
    await state.set_state(FormStates.waiting_model)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_model, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))



@dp.callback_query(FormStates.waiting_model, F.data.startswith("model_"))
async def select_model(callback: types.CallbackQuery, state: FSMContext):
    model = callback.data.split("_")[1]
    await state.update_data(model=model)
    await callback.message.answer("Choose what you want to receive:", reply_markup=output_kb)
    await state.set_state(FormStates.waiting_output_type)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_output_type, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))



@dp.callback_query(FormStates.waiting_output_type)
async def select_output_type(callback: types.CallbackQuery, state: FSMContext):
    choice = "text" if "text" in callback.data else "info"
    await state.update_data(output_type=choice)
    await callback.message.answer("🆗 All set. Transcription in progress...")

    data = await state.get_data()
    session_id = data['session_id']
    await bot.send_message(chat_id=data['chat_id'], text=f"Transcript ID: `{escape_md(session_id)}`", parse_mode="MarkdownV2")

    logger.info(f"[SEND TRANSCRIPTION TASK] {session_id}")
    await chr_tm.create_task(ChroniclerTask(data, 'transcribe_audio', None))
    #asyncio.create_task(run_transcription(data))

    await state.clear()
    await bot.send_message(chat_id=data['chat_id'], text="Session ended 🫡. Ready for another one:", reply_markup=start_kb)


# ==== CHRONICLE SAVING FLOW ====

@dp.callback_query(F.data.startswith("store_"))
async def store_decision(callback: types.CallbackQuery, state: FSMContext):
    cb_data = callback.data.split('_')
    decision = cb_data[1]
    chat_id = cb_data[2]
    session_id = cb_data[3]
    source = cb_data[4]

    if decision == "yes":
        # await callback.message.answer("Your file will be saved to the Chronicle. 🦾")
        await state.update_data(chat_id=chat_id, session_id=session_id, source=source)

        topics_list = get_topics_list()
        topic_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=topic[1], callback_data=f"topicid_{topic[0]}")]
                for topic in topics_list
            ]
        )

        await callback.message.answer("Please select a topic 🗄", reply_markup=topic_kb)
        await state.set_state(ChronicleFlow.waiting_for_topic)
    else:
        await callback.message.answer("Okay, file will not be saved.")
        await state.clear()
        await callback.message.answer("Ready for another file 🫴", reply_markup=start_kb)


@dp.callback_query(ChronicleFlow.waiting_for_topic, F.data.startswith("topicid_"))
async def topic_selected(callback: types.CallbackQuery, state: FSMContext):
    topic_id = callback.data.split('_')[1]
    await state.update_data(topic_id=topic_id)

    await callback.message.answer("Please enter a name for the dialog 💬")
    await state.set_state(ChronicleFlow.waiting_for_dialog_name)


@dp.message(ChronicleFlow.waiting_for_dialog_name)
async def dialog_name_received(message: types.Message, state: FSMContext):
    dialog_name = message.text
    await state.update_data(dialog_name=dialog_name)

    data = await state.get_data()
    chat_id = data['chat_id']
    session_id = data['session_id']
    topic_id = data['topic_id']
    source = data['source']

    #asyncio.create_task(save_to_chronicle({
    #    'chat_id': chat_id,
    #    'session_id': session_id,
    #    'topic_id': topic_id,
    #    'dialog_name': dialog_name,
    #    'source': source
    #}))
    await chr_tm.create_task(ChroniclerTask({
        'chat_id': chat_id,
        'session_id': session_id,
        'topic_id': topic_id,
        'dialog_name': dialog_name,
        'source': source
    }, 'chronicle_save', None))

    await message.answer("🦾 Your file will be saved to the Chronicle. Do you want to send another file?", reply_markup=start_kb)
    await state.clear()

from aiogram.filters import StateFilter

@dp.message(StateFilter(None))
async def catch_all(message: types.Message):
    await message.reply(
        "Please use the 'Send file' button to begin a session or /status `<id>` to get the status of your task ⛔",
        reply_markup=start_kb
    )


# Set up web server
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    logger.error("❌ Вебхук удалён")

app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Привязка webhook пути
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

def start_bot():
    web.run_app(app, host="0.0.0.0", port=8443)

if __name__ == "__main__":
    start_bot()
