# services/transcript.py
from pathlib import Path
import os
import asyncio
from application.tech_utils.notification_center import *
from application.services.sage_answer.worker import sage_answer_worker

from logging import getLogger
logger = getLogger(__name__)

async def sage_answer(data: dict):
    question_id = data['question_id']
    chat_id = data['chat_id']
    question = data['question']

    logger.info("[SAGE STARTS THINKING]")
    result = await asyncio.to_thread(sage_answer_worker, data)
    logger.info("[SAGE IS READY TO ANSWER]")

    await send_message_with_buttons(f"{result}",
                              {'Great':"feedback_5",
                               "Well done":"feedback_4",
                               "Not bad": "feedback_3",
                               "Useless": "feedback_2",
                               "Nonsense": "feedback_1"}, 
                               'sage', chat_id)

    return 0



    
    