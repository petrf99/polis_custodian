from application.dispatcher.celery_app_chr import celery_app_chr
from application.dispatcher.celery_app_sg import celery_app_sg
from application.services.transcribe_audio.service import run_transcription
from application.services.text_processing.service import process_text_service
from application.services.chronicle_save.service import save_to_chronicle
from application.services.sage_answer.service import sage_answer
from application.dispatcher.task_config import parse_policy
import asyncio

# получаем политику
transcribe_policy = parse_policy("tasks.transcribe_audio")
@celery_app_chr.task(name="tasks.transcribe_audio", bind=True, **transcribe_policy)
def transcribe_audio_task(self, data: dict):
    return asyncio.run(run_transcription(data))

transcribe_policy = parse_policy("tasks.segment_text_file")
@celery_app_chr.task(name="tasks.segment_text_file", bind=True, **transcribe_policy)
def segment_text_task(self, data: dict):
    return asyncio.run(process_text_service(data))

transcribe_policy = parse_policy("tasks.chronicle_save")
@celery_app_chr.task(name="tasks.chronicle_save", bind=True, **transcribe_policy)
def chronicle_save_task(self, data: dict):
    return asyncio.run(save_to_chronicle(data))


transcribe_policy = parse_policy("tasks.sage_answer")
@celery_app_sg.task(name="tasks.sage_answer", bind=True, **transcribe_policy)
def sage_answer_task(self, data: dict):
    return asyncio.run(sage_answer(data))