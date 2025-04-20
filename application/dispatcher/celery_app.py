from celery import Celery

celery = Celery(
    "stub",
    broker="redis://redis:6379/0",  # указываем, что брокер — это контейнер redis
)