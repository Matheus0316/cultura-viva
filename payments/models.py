from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando'),
        ('PAID', 'Pago'),
        ('FAILED', 'Falhou'),
        ('REFUNDED', 'Reembolsado'),
    ]

    PAYMENT_METHODS = [
        ('PIX', 'Pix'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamento genérico para o que está sendo pago (Pedido ou Agendamento)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    item_paid = GenericForeignKey('content_type', 'object_id')
    
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    installments = models.PositiveIntegerField(default=1, verbose_name="Parcelas")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    transaction_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID retornado pelo gateway de pagamento")
    payment_url = models.URLField(blank=True, null=True, help_text="URL para pagamento (ex: checkout pix)")
    qr_code = models.TextField(blank=True, null=True, help_text="Conteúdo do QR Code ou link do Pix Copia e Cola")
    
    # Controle de Split Pendente (quando o vendedor ainda não tem KYC aprovado)
    SPLIT_TYPE_CHOICES = [
        ('INSTANT', 'Split Imediato'),
        ('PENDING', 'Pendente (Aguardando Verificação do Vendedor)'),
        ('SENT', 'Enviado Manualmente'),
        ('NONE', 'Sem Split'),
    ]
    split_type = models.CharField(max_length=20, choices=SPLIT_TYPE_CHOICES, default='NONE')
    pending_split_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    split_subaccount_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pagamento {self.id} - {self.status} (R$ {self.amount})"

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
