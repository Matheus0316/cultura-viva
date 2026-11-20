from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

class BankAccount(models.Model):
    ACCOUNT_TYPES = [
        ('CORRENTE', 'Conta Corrente'),
        ('POUPANCA', 'Conta Poupança'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamento genérico para Artista ou Grupo
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    owner = GenericForeignKey('content_type', 'object_id')
    
    bank_name = models.CharField(max_length=100, verbose_name="Nome do Banco")
    bank_code = models.CharField(max_length=10, verbose_name="Código do Banco")
    agency = models.CharField(max_length=20, verbose_name="Agência")
    account_number = models.CharField(max_length=30, verbose_name="Número da Conta")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='CORRENTE', verbose_name="Tipo de Conta")
    pix_key = models.CharField(max_length=100, blank=True, null=True, verbose_name="Chave Pix")
    
    document_name = models.CharField(max_length=255, verbose_name="Nome do Titular")
    document_number = models.CharField(max_length=20, verbose_name="CPF/CNPJ do Titular")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone Celular")
    
    # Novos campos obrigatórios para Asaas
    email = models.EmailField(verbose_name="E-mail da Conta", blank=True, null=True)
    income_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Renda/Faturamento Mensal", default=0)
    
    address = models.CharField(max_length=255, verbose_name="Endereço", blank=True, null=True)
    address_number = models.CharField(max_length=20, verbose_name="Número", blank=True, null=True)
    complement = models.CharField(max_length=255, verbose_name="Complemento", blank=True, null=True)
    province = models.CharField(max_length=100, verbose_name="Bairro", blank=True, null=True)
    postal_code = models.CharField(max_length=20, verbose_name="CEP", blank=True, null=True)
    
    COMPANY_TYPE_CHOICES = [
        ('MEI', 'MEI'),
        ('LIMITED', 'LIMITED'),
        ('INDIVIDUAL', 'INDIVIDUAL'),
        ('ASSOCIATION', 'ASSOCIATION'),
    ]
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, blank=True, null=True, verbose_name="Tipo de Empresa")
    
    is_main = models.BooleanField(default=True, verbose_name="Conta Principal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number} ({self.document_name})"

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"

class AsaasProfile(models.Model):
    ASAAS_STATUS_CHOICES = [
        ('PENDING', 'Pendente de Verificação'),
        ('APPROVED', 'Aprovado'),
        ('REJECTED', 'Rejeitado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamento genérico para Artista ou Grupo
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    owner = GenericForeignKey('content_type', 'object_id')
    
    asaas_account_id = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="ID da Subconta Asaas")
    asaas_wallet_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Wallet ID (Split)")
    asaas_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="API Key da Subconta")
    status = models.CharField(max_length=20, choices=ASAAS_STATUS_CHOICES, default='PENDING', verbose_name="Status da Conta")
    
    # Link para o passo 5 (KYC)
    kyc_link = models.URLField(blank=True, null=True, verbose_name="Link de Verificação KYC")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Asaas Profile - {self.owner}"

    class Meta:
        verbose_name = "Perfil Asaas"
        verbose_name_plural = "Perfis Asaas"
