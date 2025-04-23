import logging
from application.dispatcher.dispatcher import dispatcher
from application.dispatcher.celery_app_sg import celery_app_sg
from urllib.parse import urlparse
import psycopg2
import os

logger = logging.getLogger(__name__)

class SageTask:
    def __init__(self, data: dict, service_name: str, input_file_name: str):
        self.service_name = service_name
        self.input_file_name = input_file_name
        self.data = data

class SageTM:
    def __init__(self):
        self.task_session_map = {}

    async def create_task(self, task: SageTask):
        logger.info("[SG TASK MANAGER: SENDING TASK TO DISPATCHER]")
        task_id = dispatcher.dispatch_task(task)
        logger.info("[SG TASK MANAGER: TASK IS BEEN SENT]")
        self.task_session_map[task.data['question_id']] = task_id
        return task_id

    async def get_status(self, question_id: str):
        try:
            task_id = self.task_session_map[question_id]
        except:
            return {'status': 'Task id not found', 'result':None}
        result = celery_app_sg.AsyncResult(task_id)
        return {
            'status': result.status,
            'result': result.result if result.successful() else None
        }

    def save_feedback(self, question_id, rate):
        POSTGRES_URL = os.getenv("POSTGRES_URL")
        result = urlparse(POSTGRES_URL)
        
        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO sage_feedback (question_id, rate)
                VALUES (%s, %s)
                ON CONFLICT (question_id) DO UPDATE SET rate = EXCLUDED.rate;
            ''', (str(question_id), int(rate)))

            conn.commit()
            logger.info("[SG. FEEDBACK SUCCESSFULLY SAVED]")

        except Exception as e:
            logger.exception(f"[SG. FEEDBACK SAVE FAILED] {e}")
            conn.rollback()

        finally:
            cursor.close()
            conn.close()


sg_tm = SageTM()