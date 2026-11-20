from celery import shared_task
from utils.email.emails import send_artist_status_email

@shared_task
def send_artist_status_email_task(artista, status):
    send_artist_status_email(artista, status)
