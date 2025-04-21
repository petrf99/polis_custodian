import logging
from application.dispatcher.dispatcher import dispatcher

logger = logging.getLogger(__name__)

class ChroniclerTask:
    def __init__(self, data: dict, service_name: str, input_file_name: str):
        self.service_name = service_name
        self.input_file_name = input_file_name
        self.data = data

class ChroniclerTM:
    async def create_task(self, task: ChroniclerTask):
        logger.info("[CHR TASK MANAGER: SENDING TASK TO DISPATCHER]")
        task_id = dispatcher.dispatch_task(task)
        logger.info("[CHR TASK MANAGER: TASK IS BEEN SENT]")
        return task_id

    async def get_status(self, task_id: str):
        from application.dispatcher.celery_app import celery_app
        result = celery_app.AsyncResult(task_id)
        return {
            'status': result.status,
            'result': result.result if result.successful() else None
        }


chr_tm = ChroniclerTM()