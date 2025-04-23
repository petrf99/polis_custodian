import logging
from application.dispatcher.dispatcher import dispatcher
from application.dispatcher.celery_app_chr import celery_app_chr

logger = logging.getLogger(__name__)

class ChroniclerTask:
    def __init__(self, data: dict, service_name: str, input_file_name: str):
        self.service_name = service_name
        self.input_file_name = input_file_name
        self.data = data

class ChroniclerTM:
    def __init__(self):
        self.task_session_map = {}

    async def create_task(self, task: ChroniclerTask):
        logger.info("[CHR TASK MANAGER: SENDING TASK TO DISPATCHER]")
        task_id = dispatcher.dispatch_task(task)
        logger.info("[CHR TASK MANAGER: TASK IS BEEN SENT]")
        self.task_session_map[task.data['session_id']] = task_id
        return task_id

    async def get_status(self, session_id: str):
        try:
            task_id = self.task_session_map[session_id]
        except:
            return {'status': 'Task id not found', 'result':None}
        result = celery_app_chr.AsyncResult(task_id)
        return {
            'status': result.status,
            'result': result.result if result.successful() else None
        }


chr_tm = ChroniclerTM()