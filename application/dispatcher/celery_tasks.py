from application.dispatcher.celery_app import celery_app
from application.services.transcribe_audio.service import run_transcription
from application.services.text_processing.service import segment_text_file
from application.services.chronicle_save.service import run_import
from application.dispatcher.task_config import parse_policy

# получаем политику
transcribe_policy = parse_policy("tasks.transcribe_audio")
@celery_app.task(name="tasks.transcribe_audio", bind=True, **transcribe_policy)
def transcribe_audio_task(data: dict):
    return run_transcription(data)

transcribe_policy = parse_policy("tasks.segment_text_file")
@celery_app.task(name="tasks.segment_text_file", bind=True, **transcribe_policy)
def segment_text_task(data: dict):
    return segment_text_file(data)

transcribe_policy = parse_policy("tasks.chronicle_save")
@celery_app.task(name="tasks.chronicle_save", bind=True, **transcribe_policy)
def chronicle_save_task(data: dict):
    return run_import(data)
