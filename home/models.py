from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4


class ChangePasswordToken(models.Model):
    email = models.EmailField()
    token = models.UUIDField(default=uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"ChangePasswordToken(user={self.user.username}, token={self.token})"
