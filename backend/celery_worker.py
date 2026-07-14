from celery import Celery
from app.config import settings

celery_app = Celery(
    "invoiceiq",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=settings.MAX_WORKERS,
)

celery_app.autodiscover_tasks(["app.workers"], related_name="document_tasks")
