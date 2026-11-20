from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamento genérico para Artista ou Grupo
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    seller = GenericForeignKey('content_type', 'object_id')
    
    name = models.CharField(max_length=200, verbose_name="Nome do Produto")
    description = models.TextField(verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço", validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(upload_to='shop/products/', verbose_name="Imagem")
    stock = models.PositiveIntegerField(default=1, verbose_name="Estoque")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

class Service(models.Model):
    DAY_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relacionamento genérico para Artista ou Grupo
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    provider = GenericForeignKey('content_type', 'object_id')
    
    name = models.CharField(max_length=200, verbose_name="Nome do Serviço")
    description = models.TextField(verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Custo do Serviço", validators=[MinValueValidator(Decimal('0.01'))])
    
    # Novos campos solicitados
    start_time = models.TimeField(verbose_name="Horário de Início", default="08:00")
    end_time = models.TimeField(verbose_name="Horário de Término", default="18:00")
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Duração (em horas)", default=1.0)
    
    # Armazenaremos os dias como uma string separada por vírgulas ou usaremos um campo de múltiplos dias
    # Para simplicidade e compatibilidade sem pacotes extras:
    available_days = models.CharField(max_length=50, help_text="Dias da semana (ex: 0,2,4 para Seg, Qua, Sex)", verbose_name="Dias Disponíveis", default="0")

    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_days_list(self):
        return [int(d) for d in self.available_days.split(',') if d.isdigit()]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Serviço/Agenda"
        verbose_name_plural = "Serviços/Agenda"
        constraints = [
            models.UniqueConstraint(fields=['content_type', 'object_id'], name='unique_service_per_provider')
        ]

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('CONFIRMED', 'Confirmado'),
        ('CANCELLED', 'Cancelado'),
        ('COMPLETED', 'Concluído'),
    ]
    
    PAYMENT_METHODS = [
        ('PIX', 'Pix'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_bookings')
    date = models.DateField(verbose_name="Data")
    time = models.TimeField(verbose_name="Hora")
    address = models.ForeignKey('perfil.Address', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Local do Serviço")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='PIX', verbose_name="Forma de Pagamento")
    installments = models.PositiveIntegerField(default=1, verbose_name="Parcelas")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor Total")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_paid(self):
        self.status = 'CONFIRMED'
        self.save()

    def __str__(self):
        return f"{self.service.name} - {self.date} {self.time}"

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PAID', 'Pago'),
        ('SHIPPED', 'Enviado'),
        ('DELIVERED', 'Entregue'),
        ('CANCELLED', 'Cancelado'),
    ]
    
    PAYMENT_METHODS = [
        ('PIX', 'Pix'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_orders')
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    shipping_address = models.ForeignKey('perfil.Address', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Endereço de Entrega")
    pickup_on_site = models.BooleanField(default=False, verbose_name="Retirar no Local")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Custo do Frete")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='PIX', verbose_name="Forma de Pagamento")
    installments = models.PositiveIntegerField(default=1, verbose_name="Parcelas")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_paid(self):
        self.status = 'PAID'
        self.save()

    def __str__(self):
        return f"Pedido {self.id} - {self.product.name}"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
