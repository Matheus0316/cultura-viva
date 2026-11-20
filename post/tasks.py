from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Post
from perfil.models import SeguidorGrupo

@shared_task
def notify_group_followers(post_id):
    try:
        post = Post.objects.get(id=post_id)
        grupo = post.grupo

        if not grupo:
            return "Post has no group."

        # Find followers of the group
        seguidores = SeguidorGrupo.objects.filter(grupo=grupo).select_related('perfil__user')

        recipient_list = [seguidor.perfil.user.email for seguidor in seguidores if seguidor.perfil.user.email]

        if not recipient_list:
            return "No followers with email found."

        subject = f'Nova publicação no grupo {grupo.name}: {post.title}'
        message = f'Olá,\n\nO grupo "{grupo.name}" tÊm uma nova publicação:\n\n"{post.title}"\n\nConfira agora na plataforma Cultura Viva Tacima.'

        # Send email to all recipients (bcc style to avoid exposing emails or individual emails?)
        # Using send_mail loop or single send with high number is risky for spam.
        # Ideally use send_mass_mail or bcc.
        # For simplicity in this task, let's send one email per user or use BCC.
        # BCC is better for privacy.

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [], # To list empty
            fail_silently=False,
            bcc=recipient_list # BCC list
        )

        return f"Notifications sent to {len(recipient_list)} followers."
    except Post.DoesNotExist:
        return "Post does not exist"
    except Exception as e:
        return f"Error sending notifications: {str(e)}"
