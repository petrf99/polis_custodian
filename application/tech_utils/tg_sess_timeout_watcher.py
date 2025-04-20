from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
import asyncio

from logging import getLogger
logger = getLogger(__name__)

# Session time out
async def start_timeout_watcher(
    state: FSMContext,
    target_state: State,
    timeout_seconds: int,
    callback_message: types.Message,
    start_kb
):
    await asyncio.sleep(timeout_seconds)
    current = await state.get_state()
    if current == target_state.state:
        session_id = await state.get_data['session_id']
        logger.info(f"[SESSION {session_id} EXPIRED DUE TO INACTIVITY]")
        await state.clear()
        await callback_message.answer(
            "⏳ Session expired due to inactivity.\nPlease start again.",
            reply_markup=start_kb
            )


