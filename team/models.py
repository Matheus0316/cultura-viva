from perfil.models import Perfil
from django.db import models

class Position(models.Model):
    name = models.CharField(max_length=100)
    importance = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['importance']

    def __str__(self):
        return self.name


class Member(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    profile = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    data_ordenacao = models.DateField(blank=True, null=True)
    inicio_paroquia = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position__importance']

    def __str__(self):
        return f"{self.profile.name} {self.position.name}"
