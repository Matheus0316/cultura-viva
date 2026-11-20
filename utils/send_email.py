from django.core.mail import send_mass_mail, send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from utils.password import generate_change_password_token


def send_change_password_email(email):
    user = User.objects.get(email=email)
    token = generate_change_password_token(email)
    link = f"http://localhost:8000/change-password/{token}/"
    subject = "Alterar senha"
    context = {
        'name': user.username,
        'link': link,
    }
    html_message = render_to_string('emails/change_password.html', context)

    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [email],
        html_message=html_message
    )


def send_notification_email(post):
    subject = f"Nova publicação em {post.grupo.name}"
    recipient_list = [seguidor.user.email for seguidor in post.grupo.seguidores.all()]

    context = {
        'post': post,
    }

    html_message = render_to_string('emails/new_post_notification.html', context)
    plain_message = strip_tags(html_message)

    if recipient_list:
        messages = [(subject, plain_message, settings.EMAIL_HOST_USER, [email],) for email in recipient_list]
        send_mass_mail(messages)


def send_remenber_event_email(email, name, event_title, event_date):
    subject = "Lembrete de Evento"
    context = {
        'name': name,
        'event_title': event_title,
        'event_date': event_date,
    }
    html_message = render_to_string('emails/reminder_event.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [email],
        html_message=html_message
    )
