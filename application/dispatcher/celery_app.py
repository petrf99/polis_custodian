# celery_app.py
import json
import os
from celery import Celery

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRIORITIES_PATH = os.path.join(BASE_DIR, 'configs/task_priorities.json')

with open(PRIORITIES_PATH, 'r') as f:
    task_priorities = json.load(f)

celery_app = Celery(
    'celery_app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1',
)

# Установка маршрутов из JSON
celery_app.conf.task_routes = {
    task_name: {'queue': queue}
    for task_name, queue in task_priorities.items()
}
