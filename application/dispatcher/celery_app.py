from celery import Celery

celery_app = Celery(
    'task_dispatcher',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.task_routes = {
    'tasks.transcribe.transcribe_audio': {'queue': 'high_priority'},
    'tasks.segment.segment_text': {'queue': 'default'},
}
