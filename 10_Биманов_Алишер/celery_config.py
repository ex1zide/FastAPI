from celery import Celery
import time
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@celery_app.task
def send_email_task(email: str):
    time.sleep(5)  # имитация долгой отправки
    print(f"Email sent to {email}")
    return f"Email sent to {email}"
