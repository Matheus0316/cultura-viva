from banking.services import get_or_create_asaas_subaccount
from utils.asaas.client import AsaasClient
from utils.asaas.tax import calculate_net_value
from banking.models import AsaasProfile
from .models import Payment
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def process_transaction_payment(item):
    """
    Gatilho de Pagamento:
    1. Garante subconta do vendedor (JIT).
    2. Cria cobrança no Asaas com Split.
    3. Registra o objeto Payment no nosso banco.
    """
    # Identificar o vendedor
    if hasattr(item, 'product'):
        seller = item.product.seller
        payer = item.buyer
    else: # Booking
        seller = item.service.provider
        payer = item.client
    
    amount = item.total_price
    
    # 1. Garante Subconta (Just-in-Time)
    asaas_profile = get_or_create_asaas_subaccount(seller)
    if not asaas_profile:
        return None, "Não foi possível configurar a conta do vendedor."

    client = AsaasClient()
    
    # 2. Verificar CPF do pagador (Obrigatório para Asaas)
    if not payer.perfil.cpf:
        return None, "Seu CPF não está cadastrado. Por favor, atualize seu perfil para continuar a compra."

    # 3. Garante Cliente (Comprador) no Asaas
    asaas_customer = client.get_or_create_customer({
        "name": payer.get_full_name() or payer.username,
        "email": payer.email,
        "cpfCnpj": (payer.perfil.cpf or "").replace('.', '').replace('-', ''),
    })
    
    if not asaas_customer or 'id' not in asaas_customer:
        return None, "Erro ao registrar comprador no sistema de pagamentos."


    # 4. Criar Cobrança no Asaas
    billing_type = "PIX" if item.payment_method == "PIX" else "CREDIT_CARD"
    installments = getattr(item, 'installments', 1)
    
    # 4. Verificar se o vendedor pode receber Split Imediato (KYC Aprovado ou Pendente)
    # No Asaas v3, subcontas PENDING também podem receber splits (ficam bloqueados até aprovação)
    use_instant_split = (asaas_profile.status in ['APPROVED', 'PENDING', 'AWAITING_APPROVAL'])
    
    payment_payload = {
        "customer": asaas_customer['id'],
        "billingType": billing_type,
        "dueDate": (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
        "description": f"Pagamento - {item}",
    }

    # Se for parcelado, usamos totalValue. Se for à vista, usamos value.
    if billing_type == "CREDIT_CARD" and installments > 1:
        payment_payload["totalValue"] = float(amount)
        payment_payload["installmentCount"] = int(installments)
    else:
        payment_payload["value"] = float(amount)

    if use_instant_split:
        payment_payload["split"] = [
            {
                "walletId": asaas_profile.asaas_wallet_id or asaas_profile.asaas_account_id,
                "percentualValue": 98.0,
                "chargeFeePayee": "RECEIVER"
            }
        ]

    # Opcional: Adicionar regras de multa/juros se necessário
    
    resp = client.create_payment(payment_payload)
    
    if 'id' in resp:
        # 5. Salvar localmente
        content_type = ContentType.objects.get_for_model(item)
        payment_obj = Payment.objects.create(
            content_type=content_type,
            object_id=item.id,
            item_paid=item,
            payer=payer,
            amount=amount,
            payment_method=item.payment_method,
            installments=installments,
            transaction_id=resp['id'],
            payment_url=resp.get('invoiceUrl'),
            status='PENDING',
            split_type='INSTANT' if use_instant_split else 'PENDING',
            split_subaccount_id=asaas_profile.asaas_account_id,
            pending_split_amount=calculate_net_value(amount, item.payment_method, installments) - (amount * Decimal('0.02'))
        )
        
        # Se for PIX, podemos pegar o QR Code (requer chamada adicional ou webhook, 
        # mas o Asaas retorna o invoiceUrl que já tem tudo)
        
        return payment_obj, None
    else:
        logger.error(f"Erro ao criar cobrança Asaas: {resp}")
        return None, resp.get('errors', [{'description': 'Erro desconhecido'}])[0]['description']

def process_pending_splits_for_seller(seller):
    """
    Varre pagamentos com split pendente para um vendedor e realiza o repasse manual
    se a subconta estiver aprovada.
    """
    from banking.services import get_or_create_asaas_subaccount
    from banking.models import AsaasProfile
    
    asaas_profile = get_or_create_asaas_subaccount(seller)
    if not asaas_profile or asaas_profile.status != 'APPROVED':
        return 0 # Ainda não aprovado
    
    # Se não temos wallet_id ainda, precisamos recuperá-lo
    if not asaas_profile.asaas_wallet_id:
        return 0
        
    pending_payments = Payment.objects.filter(
        split_subaccount_id=asaas_profile.asaas_account_id,
        split_type='PENDING',
        status='PAID'
    )
    
    total_sent = 0
    client = AsaasClient()
    
    for payment in pending_payments:
        # Tentar transferência
        resp = client.transfer_funds(asaas_profile.asaas_wallet_id, payment.pending_split_amount)
        if 'id' in resp:
            payment.split_type = 'SENT'
            payment.save()
            total_sent += 1
            logger.info(f"Split pendente repassado para {seller}: R$ {payment.pending_split_amount}")
        else:
            logger.error(f"Erro ao repassar split pendente {payment.id}: {resp}")
            
    return total_sent
