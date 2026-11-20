from celery import shared_task
from utils.send_email import send_remenber_event_email
from perfil.models import Perfil
from .models import Event


@shared_task
def send_email_remember_event(email, profile_id, event_id):
    pass
    try:
        user = Perfil.objects.get(id=profile_id)
        event = Event.objects.get(id=event_id)
        if  event.active:
            send_remenber_event_email(email, user.name, event.title, event.date.strftime('%d/%m/%Y %H:%M'))
    except Exception as e:
        return f"Error: {str(e)}"
