# dispatcher.py
import json
import os
from application.dispatcher.celery_app_chr import celery_app_chr
from logging import getLogger
logger = getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUES_PATH = os.path.join(BASE_DIR, 'configs/queues.json')

with open(QUEUES_PATH, 'r') as f:
    queues = json.load(f)

class Dispatcher:
    def __init__(self):
        # task_map теперь из приоритетов
        self.task_map = queues

    def dispatch_task(self, task_obj) -> str:
        logger.info('[DISPATCHER: TASK RECEIVED]')
        service_name = task_obj.service_name
        input_data = task_obj.data

        task_name_map = {
            'transcribe_audio': 'tasks.transcribe_audio',
            'text_processing': 'tasks.segment_text_file',
            'chronicle_save': 'tasks.chronicle_save',
        }

        if service_name not in task_name_map:
            raise ValueError(f"Unknown service: {service_name}")

        task_fullname = task_name_map[service_name]
        queue = self.task_map.get(task_fullname, 'default')

        logger.info("[DISPATCHER: SENDING TASK TO CELERY]")
        result = celery_app_chr.send_task(task_fullname, args=[input_data], queue=queue)
        logger.info("[DISPATCHER: TASK SENT]")
        return result.id

dispatcher = Dispatcher()
