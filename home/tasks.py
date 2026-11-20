from celery import shared_task
from utils.send_email import send_change_password_email

@shared_task
def send_email_reset_password(email):
    send_change_password_email(email)
