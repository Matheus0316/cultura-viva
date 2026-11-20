from django.urls import path
from .views import AsaasWebhookView

urlpatterns = [
    path('', AsaasWebhookView.as_view(), name='asaas_webhook_root'),
]
