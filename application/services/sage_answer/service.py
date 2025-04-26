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



    await send_message_with_buttons(f"🤝 Here's your answer:\n\n{result[1]}\n\nContext was retrieved from cache: {result[0]}",
                              {'Great':"feedback_5",
                               "Well done":"feedback_4",
                               "Not bad": "feedback_3",
                               "Useless": "feedback_2",
                               "Nonsense": "feedback_1"}, 
                               'sage', chat_id)
    
    if result[2]:
        await send_document(result[2], 'sage', chat_id, 'Generated context for answer')
        os.remove(result[2])
    if result[3]:
        await send_document(result[3], 'sage', chat_id, "Raw data, retrieved from the Chronicle")
        os.remove(result[3])

    return 0



    
    