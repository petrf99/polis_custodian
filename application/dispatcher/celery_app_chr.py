# celery_app.py
import json
import os
from celery import Celery

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUES_PATH = os.path.join(BASE_DIR, 'configs/queues.json')

with open(QUEUES_PATH, 'r') as f:
    queues = json.load(f)

celery_app_chr = Celery(
    'celery_app_chr',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

# Установка маршрутов из JSON
celery_app_chr.conf.task_routes = {
    task_name: {'queue': queue}
    for task_name, queue in queues.items()
}

from application.dispatcher import celery_tasks