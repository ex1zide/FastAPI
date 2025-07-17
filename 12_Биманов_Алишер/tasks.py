from celery_config import celery_app
import time

@celery_app.task
def send_email_task(email: str):
    time.sleep(5)  # имитация долгой отправки
    print(f"Email sent to {email}")
    return f"Email sent to {email}"