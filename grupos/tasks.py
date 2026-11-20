from celery import shared_task
from utils.email.emails import send_group_status_email

@shared_task
def send_group_status_email_task(grupo, status):
    send_group_status_email(grupo, status)
