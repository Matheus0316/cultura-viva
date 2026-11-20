from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Perfil
from .tasks import send_permission_email_task

@receiver(pre_save, sender=Perfil)
def check_permission_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Perfil.objects.get(pk=instance.pk)
            # Se não tinha permissão e agora tem
            if not old_instance.can_add_acervo and instance.can_add_acervo:
                # Envia email em background (ou aqui mesmo, já que é síncrono por enquanto)
                if instance.user and instance.user.email:
                    send_permission_email_task(instance.user)
        except Perfil.DoesNotExist:
            pass
