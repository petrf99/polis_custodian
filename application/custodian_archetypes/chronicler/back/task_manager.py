from application.custodian_archetypes.chronicler.back.init_db import init_db
import asyncio
from application.custodian_archetypes.chronicler.back.get_topics_list import get_topics_list
from application.services.transcribe_audio.service import run_transcription
from application.services.text_processing.service import segment_text_file
from application.services.chronicle_save.service import run_import
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ChroniclerTask:
    def __init__(self, data: dict, service_name: str, input_file_name: str):
        self.service_name = service_name
        self.input_file_name = input_file_name
        self.data = data

class ChroniclerTM:
    def __init__(self):
        self.services = {'transcribe_audio': run_transcription, 
                'text_processing': segment_text_file,
                'chronicle_save': run_import}
        self.priorities = {'transcribe_audio': 1, 
                'text_processing': 1,
                'chronicle_save': 0}
        
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def create_task(self, task: ChroniclerTask):
        session_id = task.data['session_id']
        logger.info(f"[CHR TASK MANAGER] Try to create task {session_id}")
        try:
            coro = self.services[task.service_name](task.data)
            t = asyncio.create_task(coro)
            self.running_tasks[session_id] = t
        except Exception as e:
            logger.exception(f"[CHR TASK MANAGER] Create task {session_id} failed with error: {e}")
            raise

    async def get_status(self, session_id):
        task = self.running_tasks.get(session_id)
        if not task:
            return f"Session {session_id} not found"
        if task.done():
            try:
                task.result()
                return "done"
            except Exception as e:
                return "failed"
        else:
            return "in progress"


chr_tm = ChroniclerTM()