from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import DetailView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Payment
import json
import logging

logger = logging.getLogger(__name__)

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        # Garante que o usuário só veja seus próprios pagamentos
        return super().get_queryset().filter(payer=self.request.user)

@method_decorator(csrf_exempt, name='dispatch')
class AsaasWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            event = data.get('event')
            payment_data = data.get('payment')
            
            # 1. Eventos de Pagamento
            if payment_data:
                asaas_id = payment_data.get('id')
                payment = Payment.objects.filter(transaction_id=asaas_id).first()
                
                if payment:
                    if event in ['PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED']:
                        payment.status = 'PAID'
                        
                        # Se for um split pendente, calcular o valor real baseado no valor líquido do Asaas
                        if payment.split_type == 'PENDING':
                            # O Asaas envia o netValue (valor após as taxas dele)
                            net_value = payment_data.get('netValue')
                            if net_value:
                                from decimal import Decimal
                                payment.pending_split_amount = Decimal(str(net_value)) * Decimal('0.98')
                        
                        payment.save()
                        
                        # Disparar atualização do item relacionado (Pedido ou Agendamento)
                        if payment.item_paid and hasattr(payment.item_paid, 'mark_as_paid'):
                            payment.item_paid.mark_as_paid()
                            logger.info(f"Item {payment.item_paid} marcado como pago/confirmado via Webhook")
                    
                    elif event == 'PAYMENT_OVERDUE':
                        payment.status = 'FAILED'
                        payment.save()
                    
                    elif event == 'PAYMENT_REFUNDED':
                        payment.status = 'REFUNDED'
                        payment.save()
                    
                    elif event == 'PAYMENT_DELETED':
                        payment.status = 'FAILED'
                        payment.save()

            # 2. Eventos de Status de Conta (Subcontas)
            if event in ['ACCOUNT_STATUS', 'ACCOUNT_STATUS_CHANGED']:
                account_data = data.get('account')
                if account_data:
                    from banking.models import AsaasProfile
                    from .services import process_pending_splits_for_seller
                    
                    acc_id = account_data.get('id')
                    new_status = account_data.get('status')
                    
                    profile = AsaasProfile.objects.filter(asaas_account_id=acc_id).first()
                    if profile:
                        old_status = profile.status
                        profile.status = new_status
                        profile.save()
                        
                        if new_status == 'APPROVED' and old_status != 'APPROVED':
                            # Libera os splits retidos
                            process_pending_splits_for_seller(profile.owner)
                            logger.info(f"Subconta {acc_id} aprovada! Splits pendentes processados.")

            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Erro ao processar Webhook Asaas: {str(e)}")
            return HttpResponse(status=400)
