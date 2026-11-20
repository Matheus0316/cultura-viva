from .models import AsaasProfile, BankAccount
from utils.asaas.client import AsaasClient
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_or_create_asaas_subaccount(seller):
    """
    Fluxo Just-in-Time: Garante que o vendedor tenha uma subconta no Asaas.
    Cria a subconta no momento da primeira venda se ela não existir.
    """
    content_type = ContentType.objects.get_for_model(seller)
    profile = AsaasProfile.objects.filter(content_type=content_type, object_id=seller.id).first()
    
    # 2. Busca dados bancários locais
    bank_info = BankAccount.objects.filter(content_type=content_type, object_id=seller.id, is_main=True).first()
    if not bank_info:
        logger.error(f"Tentativa de criar subconta Asaas sem dados bancários para {seller}")
        return None

    client = AsaasClient()
    doc = bank_info.document_number.replace('.', '').replace('-', '').replace('/', '')

    # 3. Se já temos um ID local, verificamos se ele é válido (ou simplesmente prosseguimos)
    # Mas para evitar o erro "Wallet inexistente", vamos validar se a conta existe no Asaas pelo CPF
    existing_accounts = client.list_subaccounts(cpfCnpj=doc)
    if existing_accounts.get('data') and len(existing_accounts['data']) > 0:
        asaas_data = existing_accounts['data'][0]
        if not profile:
            profile = AsaasProfile.objects.create(content_type=content_type, object_id=seller.id, owner=seller)
        
        profile.asaas_account_id = asaas_data['id']
        profile.asaas_wallet_id = asaas_data.get('walletId')
        profile.asaas_api_key = asaas_data.get('apiKey') or profile.asaas_api_key
        # Atualizar status real do Asaas
        old_status = profile.status
        profile.status = asaas_data.get('status', 'PENDING')
        logger.info(f"Subconta Asaas {profile.asaas_account_id} status: {profile.status}")
        
        # 3.1 Se não temos a API Key da subconta, tentamos gerar uma agora (usando a conta principal)
        if not profile.asaas_api_key:
            key_resp = client.create_subaccount_api_key(profile.asaas_account_id)
            if 'apiKey' in key_resp:
                profile.asaas_api_key = key_resp['apiKey']
        
        profile.save()

        # Se acabou de ser aprovado, processar repasses retidos
        if profile.status == 'APPROVED' and old_status != 'APPROVED':
            from payments.services import process_pending_splits_for_seller
            process_pending_splits_for_seller(seller)

        # 3.1 Garantir que o link de KYC exista se a conta não estiver aprovada
        if profile.status != 'APPROVED' and not profile.kyc_link and profile.asaas_api_key:
            try:
                sub_client = AsaasClient(api_key=profile.asaas_api_key)
                onboarding_resp = sub_client.get_onboarding_link()
                logger.info(f"Onboarding response para {seller}: {onboarding_resp}")
                profile.kyc_link = onboarding_resp.get('onboardingUrl')
                
                # Fallback: Se não veio onboardingUrl mas estamos em Sandbox, 
                # pode ser que precisemos apenas forçar a aprovação
                if not profile.kyc_link and 'sandbox' in settings.ASAAS_BASE_URL:
                    logger.info("Sandbox detectado sem onboardingUrl. Tentando auto-aprovação...")
                    sub_client.sandbox_approve_account()
                    profile.status = 'APPROVED'
                
                profile.save()
            except Exception as e:
                logger.error(f"Erro ao recuperar link KYC para conta existente {profile.asaas_account_id}: {e}")
            
        return profile

    # 4. Se chegamos aqui e já temos um profile com ID, mas ele não foi achado acima, 
    # significa que o ID no banco é de outro ambiente ou foi deletado. 
    # Vamos limpar e criar de novo.
    if profile:
        profile.asaas_account_id = None
        profile.save()
    
    is_pj = len(doc) > 11
    
    payload = {
        "name": bank_info.document_name,
        "cpfCnpj": doc,
        "email": bank_info.email or f"{seller.id.hex[:6]}cvtacima@gmail.com",
        "mobilePhone": (bank_info.phone or getattr(seller, 'whatsapp', '')).replace(' ', '').replace('-', '').replace('(', '').replace(')', ''),
        "incomeValue": float(bank_info.income_value),
        "address": bank_info.address,
        "addressNumber": bank_info.address_number,
        "complement": bank_info.complement,
        "province": bank_info.province,
        "postalCode": bank_info.postal_code.replace('-', '').replace(' ', ''),
        "webhooks": [
            {
                "name": "Webhook Cultura Viva",
                "url": getattr(settings, 'WEBHOOK_BASE_URL', 'https://culturavivatacima.com.br') + "/api/webhook/asaas/", 
                "email": settings.EMAIL_HOST_USER,
                "sendType": "SEQUENTIALLY",
                "interrupted": False,
                "enabled": True,
                "apiVersion": 3,
                "events": [
                    "PAYMENT_CREATED", 
                    "PAYMENT_UPDATED", 
                    "PAYMENT_CONFIRMED", 
                    "PAYMENT_RECEIVED", 
                    "PAYMENT_OVERDUE", 
                    "PAYMENT_DELETED", 
                    "PAYMENT_REFUNDED"
                ]
            }
        ]
    }

    if is_pj:
        payload["companyType"] = bank_info.company_type or "MEI"
    elif bank_info.birth_date:
        payload["birthDate"] = bank_info.birth_date.isoformat()

    resp = client.create_subaccount(payload)
    
    if 'id' in resp:
        if not profile:
            profile = AsaasProfile.objects.create(
                content_type=content_type, 
                object_id=seller.id,
                owner=seller
            )
            
        profile.asaas_account_id = resp['id']
        profile.asaas_wallet_id = resp.get('walletId')
        profile.asaas_api_key = resp.get('apiKey')
        
        # Busca o link de KYC (Onboarding) usando a chave da subconta
        if profile.asaas_api_key:
            sub_client = AsaasClient(api_key=profile.asaas_api_key)
            onboarding_resp = sub_client.get_onboarding_link()
            profile.kyc_link = onboarding_resp.get('onboardingUrl')
            print(profile.kyc_link)
            
        profile.status = 'PENDING'
        profile.save()
        return profile
    else:
        logger.error(f"Erro ao criar subconta Asaas para {seller}: {resp}")
        return None
