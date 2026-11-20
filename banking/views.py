from django.shortcuts import render, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from .models import BankAccount
from .forms import BankAccountForm
from artistas.models import Artista
from grupos.models import Grupo
from django.http import HttpResponse
from django.utils.text import slugify

class UpdateBankAccountView(LoginRequiredMixin, View):
    def post(self, request, seller_type, seller_id):
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
            if obj.user != request.user:
                return HttpResponse("Não autorizado", status=403)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            if not obj.membros.filter(perfil=request.user.perfil, position__position__iexact='Líder').exists():
                return HttpResponse("Não autorizado", status=403)

        content_type = ContentType.objects.get_for_model(obj)
        bank_account = BankAccount.objects.filter(content_type=content_type, object_id=obj.id).first()
        
        form = BankAccountForm(request.POST, instance=bank_account)
        if form.is_valid():
            bank_account = form.save(commit=False)
            bank_account.content_type = content_type
            bank_account.object_id = obj.id
            
            # Endereço: usa o endereço sede/localização do artista/grupo (mantido automático)
            
            # Endereço: usa o endereço sede/localização do artista/grupo
            if obj.address:
                bank_account.address = obj.address.street
                bank_account.address_number = obj.address.number
                bank_account.province = obj.address.neighborhood
                bank_account.postal_code = obj.address.zip_code
                # Complemento não existe no modelo Address, fica em branco ou mantém o que estiver
            
            bank_account.save()
            
            # Retornamos apenas um script para fechar o modal
            # O card no fundo se atualizará pelo evento 'bankAccountUpdated'
            response = HttpResponse('<script>document.getElementById("bank-modal").remove();</script>')
            response['HX-Trigger'] = 'bankAccountUpdated'
            return response
        
        return render(request, 'banking/partials/bank_account_form.html', {
            'form': form, 
            'obj': obj, 
            'seller_type': seller_type
        })

class BankAccountFormView(LoginRequiredMixin, View):
    def get(self, request, seller_type, seller_id):
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            
        content_type = ContentType.objects.get_for_model(obj)
        bank_account = BankAccount.objects.filter(content_type=content_type, object_id=obj.id).first()
        form = BankAccountForm(instance=bank_account)
        
        return render(request, 'banking/partials/bank_account_form.html', {
            'form': form, 
            'obj': obj, 
            'seller_type': seller_type
        })

class BankAccountInfoView(LoginRequiredMixin, View):
    def get(self, request, seller_type, seller_id):
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            
        content_type = ContentType.objects.get_for_model(obj)
        bank_account = BankAccount.objects.filter(content_type=content_type, object_id=obj.id).first()
        
        return render(request, 'banking/partials/bank_account_info.html', {
            'bank_account': bank_account, 
            'obj': obj, 
            'seller_type': seller_type
        })
