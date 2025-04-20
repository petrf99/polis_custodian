from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
import datetime
import uuid
from application.services.transcribe_audio.service import run_transcription
from application.tech_utils.tg_sess_timeout_watcher import start_timeout_watcher
from front.create_buttons import create_buttons
from application.services.chronicle_save.service import save_to_chronicle
from application.custodian_archetypes.chronicler.back.get_topics_list import get_topics_list

from logging import getLogger
logger = getLogger(__name__)


# FSM: all file sending session states
class FormStates(StatesGroup):
    waiting_language = State()
    waiting_model = State()
    waiting_temperature = State()
    waiting_output_type = State()
    waiting_audio = State()
    waiting_store_decision = State()

# FSM: all saving to chronicle session states
class ChronicleFlow(StatesGroup):
    waiting_for_topic = State()
    waiting_for_dialog_name = State()
 

# Set up bot
BOT_TOKEN = os.getenv("CHRONICLER_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Set up some params
timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", 600))

# Create buttons
start_kb, language_kb, model_kb, temp_kb, output_kb = create_buttons()

topics_list = None

# Entry point
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Welcome to the Polis Chronicler Bot 🏛️\nHere you can send your audio dialogues to transcribe them and record into our Chronicle.\nClick the button below to begin.",
        reply_markup=start_kb
    )
    logger.info('[BOT IS WORKING]')

# Prevent users from spamming random messages outside the flow
@dp.message(F.state == default_state)
async def catch_all(message: types.Message):
    await message.reply("Please use the button 'Send file' to start a session. Everything else will be ignored. ⛔",
    reply_markup=start_kb
    )

# Session start
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

    await callback.message.answer("Choose the language of your audio:", reply_markup=language_kb)
    await state.set_state(FormStates.waiting_language)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_language, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))


@dp.callback_query(FormStates.waiting_language, F.data.startswith("lang_"))
async def select_language(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    await callback.message.answer("Choose the model size (the bigger size - the longer time):", reply_markup=model_kb)
    await state.set_state(FormStates.waiting_model)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_model, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))


@dp.callback_query(FormStates.waiting_model, F.data.startswith("model_"))
async def select_model(callback: types.CallbackQuery, state: FSMContext):
    model = callback.data.split("_")[1]
    await state.update_data(model=model)
    await callback.message.answer(
        "Select temperature (controls transcription creativity):",
        reply_markup=temp_kb
    )
    await state.set_state(FormStates.waiting_temperature)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_temperature, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))


@dp.callback_query(FormStates.waiting_temperature, F.data.startswith("temp_"))
async def select_temperature(callback: types.CallbackQuery, state: FSMContext):
    temp_val = callback.data.split("_")[1]
    temperature = None if temp_val == "default" else float(temp_val)
    await state.update_data(temperature=temperature)
    await callback.message.answer("Choose what you want to receive:", reply_markup=output_kb)
    await state.set_state(FormStates.waiting_output_type)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_output_type, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))


@dp.callback_query(FormStates.waiting_output_type)
async def select_output_type(callback: types.CallbackQuery, state: FSMContext):
    choice = "text" if "text" in callback.data else "info"
    await state.update_data(output_type=choice)
    await callback.message.answer("🆗 Great. Now send me your audio file or voice message.")
    await state.set_state(FormStates.waiting_audio)

    asyncio.create_task(start_timeout_watcher(state=state, target_state=FormStates.waiting_audio, timeout_seconds=timeout_seconds, callback_message=callback.message, start_kb=start_kb))

@dp.message(FormStates.waiting_audio, F.voice | F.audio | F.document)
async def receive_audio(message: types.Message, state: FSMContext):
    file = message.voice or message.audio or message.document

    if not file:
        await message.reply("Please send an actual audio file or voice message.")
        return

    if message.document and not message.document.mime_type.startswith("audio/"):
        await message.reply("This doesn't look like an audio file. Only audio formats are supported.")
        return

    await message.reply("✔️ Your file has been received. You will be notified once the transcript is done. 🔔")
    await state.update_data(file_id=file.file_id)
    await state.update_data(chat_id=message.chat.id)

    data = await state.get_data()
    session_id = data['session_id']
    await bot.send_message(
            chat_id=data['chat_id'],
            text=f"Transcript ID: {session_id}")
    
    logger.info(f"[SEND TRANSCRIPTION TASK] {data['session_id']}")
    asyncio.create_task(run_transcription(bot, data))


    logger.info(f"[END SESSION] {data['session_id']}")
    logger.info(f"[SESSION DATA] {data}")

    chat_id = data['chat_id']

    await state.clear()
    await bot.send_message(chat_id=chat_id, text="Session ended 🫡. Ready for another one:", reply_markup=start_kb)


@dp.callback_query(F.data.startswith("store_"))
async def store_decision(callback: types.CallbackQuery, state: FSMContext):
    cb_data = callback.data.split('_')
    decision = cb_data[1]
    chat_id = cb_data[2]
    session_id = cb_data[3]
    source = cb_data[4]

    if decision == "yes":
        await callback.message.answer("Your file will be saved to the Chronicle. 🦾")

        # сохраняем chat_id и session_id
        await state.update_data(chat_id=chat_id, session_id=session_id, source=source)

        topics_list = get_topics_list()  # получи список топиков

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

    # собираем всё и передаём в save_to_chronicle
    data = await state.get_data()
    chat_id = data['chat_id']
    session_id = data['session_id']
    topic_id = data['topic_id']
    source = data['source']

    await message.answer("Uploading to Chronicle... 📤")

    asyncio.create_task(save_to_chronicle(
        bot,
        {'chat_id':chat_id,
        'session_id':session_id,
        'topic_id':topic_id,
        'dialog_name':dialog_name,
        'source':source}
    ))

    await message.answer("Do you want to send another file? 🫴", reply_markup=start_kb)

    await state.clear()

# Main loop
async def start_bot():
    logger.info('[START BOT POLLING]')
    await dp.start_polling(bot)
