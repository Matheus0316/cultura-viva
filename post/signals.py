from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Post
from .tasks import notify_group_followers

@receiver(post_save, sender=Post)
def notify_new_post(sender, instance, created, **kwargs):
    if created:
        # Use on_commit to avoid race conditions where the task starts before the DB commit
        transaction.on_commit(lambda: notify_group_followers.delay(instance.id))
