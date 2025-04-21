# dispatcher.py
import json
import os
from application.dispatcher.celery_app import celery_app

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRIORITIES_PATH = os.path.join(BASE_DIR, 'configs/task_priorities.json')

with open(PRIORITIES_PATH, 'r') as f:
    task_priorities = json.load(f)

class Dispatcher:
    def __init__(self):
        # task_map теперь из приоритетов
        self.task_map = task_priorities

    def dispatch_task(self, task_obj) -> str:
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

        result = celery_app.send_task(task_fullname, args=[input_data], queue=queue)
        return result.id

dispatcher = Dispatcher()
