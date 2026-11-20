from celery import shared_task
from utils.email.emails import send_permission_email, send_custom_notification_email


@shared_task
def send_permission_email_task(user):
    send_permission_email(user)

@shared_task
def send_custom_notification_email_task(user, title, message, action_url=None, action_text=None):
    send_custom_notification_email(user, title, message, action_url, action_text)