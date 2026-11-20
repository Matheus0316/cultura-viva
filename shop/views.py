from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, UpdateView, DeleteView, View, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from .models import Product, Service, Booking, Order
from .forms import ProductForm, ServiceForm
from artistas.models import Artista
from grupos.models import Grupo
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal
from utils.geo.distance import haversine_distance
from perfil.models import Address
from payments.services import process_transaction_payment
from utils.asaas.tax import calculate_net_value, calculate_gross_up_credit_card, calculate_gross_up_pix
from logging import getLogger

logger = getLogger(__name__)

class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seller = self.object.seller
        is_owner = False
        if self.request.user.is_authenticated:
            if isinstance(seller, Artista):
                is_owner = seller.user == self.request.user
            elif isinstance(seller, Grupo):
                is_owner = seller.membros.filter(perfil=self.request.user.perfil, position__position__iexact='Líder').exists()
        
        context['is_owner'] = is_owner
        context['seller_lat'] = float(seller.address.latitude) if seller.address and seller.address.latitude else None
        context['seller_lon'] = float(seller.address.longitude) if seller.address and seller.address.longitude else None
        context['delivery_enabled'] = seller.delivery_enabled
        context['shipping_cost_per_km'] = float(seller.shipping_cost_per_km)
        context['free_shipping_threshold_km'] = float(seller.free_shipping_threshold_km)

        if self.request.user.is_authenticated:
            context['user_addresses'] = self.request.user.addresses.all()

        context['related_products'] = Product.objects.filter(
            content_type=self.object.content_type,
            object_id=self.object.object_id
        ).exclude(id=self.object.id)[:4]
        
        if self.request.user.is_authenticated:
            context['user_addresses'] = self.request.user.addresses.all().order_by('-is_main')
        return context

class ServiceDetailView(DetailView):
    model = Service
    template_name = 'shop/service_detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider = self.object.provider
        is_owner = False
        if self.request.user.is_authenticated:
            if isinstance(provider, Artista):
                is_owner = provider.user == self.request.user
            elif isinstance(provider, Grupo):
                is_owner = provider.membros.filter(perfil=self.request.user.perfil, position__position__iexact='Líder').exists()
        
        context['is_owner'] = is_owner
        context['related_services'] = Service.objects.filter(
            content_type=self.object.content_type,
            object_id=self.object.object_id
        ).exclude(id=self.object.id)[:4]
        
        if self.request.user.is_authenticated:
            context['user_addresses'] = self.request.user.addresses.all().order_by('-is_main')
        return context

class SellerPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        seller_type = self.kwargs.get('seller_type')
        seller_id = self.kwargs.get('seller_id')
        
        if seller_type == 'artista':
            artista = get_object_or_404(Artista, id=seller_id)
            return artista.user == self.request.user
        elif seller_type == 'grupo':
            grupo = get_object_or_404(Grupo, id=seller_id)
            return grupo.membros.filter(perfil=self.request.user.perfil, position__position__iexact='Líder').exists()
        return False

class ProductOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        product = get_object_or_404(Product, id=self.kwargs.get('pk'))
        seller = product.seller
        if isinstance(seller, Artista):
            return seller.user == self.request.user
        elif isinstance(seller, Grupo):
            return seller.membros.filter(perfil=self.request.user.perfil, position__position__iexact='Líder').exists()
        return False

class ServiceOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        service = get_object_or_404(Service, id=self.kwargs.get('pk'))
        provider = service.provider
        if isinstance(provider, Artista):
            return provider.user == self.request.user
        elif isinstance(provider, Grupo):
            return provider.membros.filter(perfil=self.request.user.perfil, position__position__iexact='Líder').exists()
        return False

class ProductCreateView(LoginRequiredMixin, SellerPermissionMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'

    def form_valid(self, form):
        seller_type = self.kwargs.get('seller_type')
        seller_id = self.kwargs.get('seller_id')
        
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            
        form.instance.content_type = ContentType.objects.get_for_model(obj)
        form.instance.object_id = obj.id
        messages.success(self.request, "Produto adicionado com sucesso!")
        return super().form_valid(form)

    def get_success_url(self):
        seller_type = self.kwargs.get('seller_type')
        seller_id = self.kwargs.get('seller_id')
        if seller_type == 'artista':
            return reverse('artistas:artista_detail', kwargs={'pk': seller_id})
        return reverse('grupos:grupo_detail', kwargs={'id': seller_id})

class ProductUpdateView(LoginRequiredMixin, ProductOwnerMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'

    def form_valid(self, form):
        messages.success(self.request, "Produto atualizado com sucesso!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('shop:product_detail', kwargs={'pk': self.object.id})

class ProductDeleteView(LoginRequiredMixin, ProductOwnerMixin, DeleteView):
    model = Product
    template_name = 'shop/product_confirm_delete.html'

    def get_success_url(self):
        messages.warning(self.request, "Produto removido.")
        obj = self.object.seller
        if isinstance(obj, Artista):
            return reverse('artistas:artista_detail', kwargs={'pk': obj.id})
        return reverse('grupos:grupo_detail', kwargs={'id': obj.id})

class ServiceCreateView(LoginRequiredMixin, SellerPermissionMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'shop/service_form.html'

    def form_valid(self, form):
        seller_type = self.kwargs.get('seller_type')
        seller_id = self.kwargs.get('seller_id')
        
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            
        form.instance.content_type = ContentType.objects.get_for_model(obj)
        form.instance.object_id = obj.id
        messages.success(self.request, "Serviço/Horário adicionado com sucesso!")
        return super().form_valid(form)

    def get_success_url(self):
        seller_type = self.kwargs.get('seller_type')
        seller_id = self.kwargs.get('seller_id')
        if seller_type == 'artista':
            return reverse('artistas:artista_detail', kwargs={'pk': seller_id})
        return reverse('grupos:grupo_detail', kwargs={'id': seller_id})

class ServiceUpdateView(LoginRequiredMixin, ServiceOwnerMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'shop/service_form.html'

    def form_valid(self, form):
        messages.success(self.request, "Serviço atualizado!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('shop:service_detail', kwargs={'pk': self.object.id})

class ServiceDeleteView(LoginRequiredMixin, ServiceOwnerMixin, DeleteView):
    model = Service
    template_name = 'shop/service_confirm_delete.html'

    def get_success_url(self):
        messages.warning(self.request, "Serviço removido.")
        obj = self.object.provider
        if isinstance(obj, Artista):
            return reverse('artistas:artista_detail', kwargs={'pk': obj.id})
        return reverse('grupos:grupo_detail', kwargs={'id': obj.id})

class ServiceSettingsView(LoginRequiredMixin, SellerPermissionMixin, View):
    template_name = 'shop/service_form.html'

    def get(self, request, seller_type, seller_id):
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            
        content_type = ContentType.objects.get_for_model(obj)
        service, created = Service.objects.get_or_create(
            content_type=content_type,
            object_id=obj.id,
            defaults={
                'name': f'Agenda de {obj.name}',
                'description': f'Serviços e agendamentos culturais de {obj.name}.',
                'price': Decimal('50.00'),
            }
        )
        
        form = ServiceForm(instance=service)
        return render(request, self.template_name, {
            'form': form, 
            'obj': obj, 
            'is_settings': True,
            'seller_type': seller_type,
            'seller_id': seller_id
        })

    def post(self, request, seller_type, seller_id):
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            
        content_type = ContentType.objects.get_for_model(obj)
        service = get_object_or_404(Service, content_type=content_type, object_id=obj.id)
        
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Configurações da agenda atualizadas com sucesso!")
            if seller_type == 'artista':
                return redirect('artistas:artista_detail', pk=seller_id)
            return redirect('grupos:grupo_detail', id=seller_id)
            
        return render(request, self.template_name, {
            'form': form, 
            'obj': obj, 
            'is_settings': True,
            'seller_type': seller_type,
            'seller_id': seller_id
        })

class ProcessPurchaseView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        address_selector = request.POST.get('address_selector')
        payment_method = request.POST.get('payment_method', 'PIX')
        installments = int(request.POST.get('installments', 1))
        
        if quantity > product.stock:
            messages.error(request, f"Quantidade solicitada ({quantity}) excede o estoque disponível ({product.stock}).")
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        if quantity <= 0:
            messages.error(request, "A quantidade deve ser pelo menos 1.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        pickup_on_site = address_selector == 'pickup'
        shipping_address = None
        shipping_cost = Decimal('0.00')
        
        if not pickup_on_site:
            if not address_selector:
                messages.error(request, "Por favor, selecione um endereço de entrega ou escolha retirar no local.")
                return redirect(request.META.get('HTTP_REFERER', '/'))
            shipping_address = get_object_or_404(Address, id=address_selector, perfil__user=request.user)
            
            # Cálculo de frete
            seller = product.seller
            if hasattr(seller, 'address') and seller.address and seller.address.latitude and seller.address.longitude and shipping_address.latitude and shipping_address.longitude:
                dist = haversine_distance(
                    seller.address.latitude, seller.address.longitude,
                    shipping_address.latitude, shipping_address.longitude
                )
                if Decimal(str(dist)) > seller.free_shipping_threshold_km:
                    shipping_cost = (Decimal(str(dist)) * seller.shipping_cost_per_km).quantize(Decimal('0.01'))

        total_price = (product.price * quantity) + shipping_cost
        
        if payment_method == 'CREDIT_CARD':
            total_price = calculate_gross_up_credit_card(total_price, installments)
        elif payment_method == 'PIX':
            total_price = calculate_gross_up_pix(total_price)
        
        order = Order.objects.create(
            product=product,
            buyer=request.user,
            quantity=quantity,
            total_price=total_price,
            shipping_address=shipping_address,
            pickup_on_site=pickup_on_site,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            installments=installments,
            status='PENDING'
        )
        
        # Decrementa estoque
        product.stock -= quantity
        product.save()
        
        # Inicia Gatilho de Pagamento
        payment, error = process_transaction_payment(order)
        if payment:
            return redirect('payments:payment_detail', pk=payment.id)
        else:
            # Se falhar no Asaas, removemos o pedido para evitar lixo no banco
            order.delete()
            # Devolvemos o estoque
            product.stock += quantity
            product.save()
            messages.error(request, f"Erro ao gerar pagamento: {error}")
            return redirect(request.META.get('HTTP_REFERER', '/'))

class ProcessBookingView(LoginRequiredMixin, View):
    def post(self, request, service_id):
        service = get_object_or_404(Service, id=service_id)
        date = request.POST.get('date')
        time = request.POST.get('time')
        address_id = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method', 'PIX')
        installments = int(request.POST.get('installments', 1))
        
        if not date or not time:
            messages.error(request, "Por favor, selecione data e hora.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        if not address_id:
            messages.error(request, "Por favor, selecione o local para o serviço.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        address = get_object_or_404(request.user.addresses, id=address_id)
            
        total_price = service.price
        if payment_method == 'CREDIT_CARD':
            total_price = calculate_gross_up_credit_card(total_price, installments)
        elif payment_method == 'PIX':
            total_price = calculate_gross_up_pix(total_price)

        booking = Booking.objects.create(
            service=service,
            client=request.user,
            date=date,
            time=time,
            address=address,
            payment_method=payment_method,
            installments=installments,
            total_price=total_price,
            status='PENDING'
        )
        
        # Inicia Gatilho de Pagamento
        payment, error = process_transaction_payment(booking)
        if payment:
            return redirect('payments:payment_detail', pk=payment.id)
        else:
            # Se falhar no Asaas, removemos o agendamento
            booking.delete()
            messages.error(request, f"Erro ao gerar pagamento: {error}")
            return redirect(request.META.get('HTTP_REFERER', '/'))

class GetAvailableSlotsView(View):
    def get(self, request, service_id):
        service = get_object_or_404(Service, id=service_id)
        date_str = request.GET.get('date')
        
        if not date_str:
            return JsonResponse({'error': 'Data não fornecida'}, status=400)
            
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido'}, status=400)
            
        day_of_week = target_date.weekday()
        allowed_days = service.get_days_list()
        
        slots = []
        if day_of_week in allowed_days:
            start_dt = datetime.combine(target_date, service.start_time)
            end_dt = datetime.combine(target_date, service.end_time)
            duration_minutes = float(service.duration_hours) * 60
            
            # Busca agendamentos já confirmados/pendentes para esta data
            bookings = service.bookings.filter(date=target_date).exclude(status='CANCELLED')
            booked_times = [b.time.strftime('%H:%M') for b in bookings]
            
            current_dt = start_dt
            while current_dt + timedelta(minutes=duration_minutes) <= end_dt:
                time_str = current_dt.strftime('%H:%M')
                slots.append({
                    'time': time_str,
                    'available': time_str not in booked_times
                })
                current_dt += timedelta(minutes=duration_minutes)
            
        return JsonResponse({
            'slots': slots,
            'allowed_weekdays': allowed_days
        })

class SalesDashboardView(LoginRequiredMixin, SellerPermissionMixin, View):
    def get(self, request, seller_type, seller_id):
        from banking.models import AsaasProfile, BankAccount
        if seller_type == 'artista':
            obj = get_object_or_404(Artista, id=seller_id)
        else:
            obj = get_object_or_404(Grupo, id=seller_id)
            
        content_type = ContentType.objects.get_for_model(obj)
        from banking.services import get_or_create_asaas_subaccount
        asaas_profile = get_or_create_asaas_subaccount(obj)
        bank_account = BankAccount.objects.filter(content_type=content_type, object_id=obj.id).first()
        
        # Cálculos Financeiros
        from django.db.models import Sum
        from payments.models import Payment
        
        orders = Order.objects.filter(
            product__content_type=content_type,
            product__object_id=obj.id
        ).order_by('-created_at')
        
        bookings = Booking.objects.filter(
            service__content_type=content_type,
            service__object_id=obj.id
        ).order_by('-date', '-time')

        # Função auxiliar para estimar ganho líquido (98% do líquido do Asaas)
        def estimate_net(item):
            net_asaas = calculate_net_value(item.total_price, item.payment_method, item.installments)
            return (net_asaas * Decimal('0.98')).quantize(Decimal('0.01'))

        for order in orders:
            order.net_earning = estimate_net(order)
        for booking in bookings:
            booking.net_earning = estimate_net(booking)

        # 1. Saldo Retido (Tudo que será repassado para o vendedor assim que ele for aprovado)
        # Filtramos por pagamentos que ainda estão com split 'PENDING'
        pending_retained = Payment.objects.filter(
            split_subaccount_id=asaas_profile.asaas_account_id if asaas_profile else 'NON_EXISTENT',
            split_type='PENDING',
            status='PAID' # Mantemos PAID para o que já caiu, mas vamos somar o PENDING separadamente se necessário
        ).aggregate(total=Sum('pending_split_amount'))['total'] or Decimal('0.00')

        # Valor que "vai cair" (Vendas feitas mas que o cliente ainda não pagou o boleto/pix)
        expected_balance = Payment.objects.filter(
            split_subaccount_id=asaas_profile.asaas_account_id if asaas_profile else 'NON_EXISTENT',
            split_type='PENDING',
            status='PENDING'
        ).aggregate(total=Sum('pending_split_amount'))['total'] or Decimal('0.00')

        # Valor total que será repassado após aprovação
        total_retained = pending_retained + expected_balance

        # 2. Lucro Acumulado (Total de vendas confirmadas)
        paid_orders_sum = orders.filter(status='PAID').aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        paid_bookings_sum = bookings.filter(status='PAID').aggregate(total=Sum('total_price'))['total'] or Decimal('0.00')
        total_profit = (paid_orders_sum + paid_bookings_sum) * Decimal('0.98')

        # 3. Saldo Disponível no Asaas (Subconta)
        asaas_balance = Decimal('0.00')
        if asaas_profile and asaas_profile.asaas_api_key:
            try:
                from utils.asaas.client import AsaasClient
                sub_client = AsaasClient(api_key=asaas_profile.asaas_api_key)
                balance_resp = sub_client.get_balance()
                asaas_balance = Decimal(str(balance_resp.get('balance', 0)))
            except Exception as e:
                logger.error(f"Erro ao buscar saldo Asaas para {obj}: {e}")

        # 4. Dados para o Gráfico (Últimos 30 dias)
        from django.db.models.functions import TruncDate
        last_30_days = datetime.now() - timedelta(days=30)
        
        sales_by_day = orders.filter(created_at__gte=last_30_days, status='PAID').annotate(date=TruncDate('created_at')).values('date').annotate(total=Sum('total_price')).order_by('date')
        bookings_by_day = bookings.filter(date__gte=last_30_days, status='PAID').values('date').annotate(total=Sum('total_price')).order_by('date')

        # Mesclar dados para o gráfico
        chart_data = {}
        for s in sales_by_day:
            date_str = s['date'].strftime('%d/%m')
            chart_data[date_str] = float(s['total'])
        for b in bookings_by_day:
            date_str = b['date'].strftime('%d/%m')
            chart_data[date_str] = chart_data.get(date_str, 0) + float(b['total'])

        context = {
            'obj': obj,
            'orders': orders,
            'bookings': bookings,
            'seller_type': seller_type,
            'seller_id': seller_id,
            'asaas_profile': asaas_profile,
            'bank_account': bank_account,
            
            # Métricas
            'total_profit': total_profit,
            'total_retained': total_retained,
            'pending_retained': pending_retained,
            'expected_balance': expected_balance,
            'asaas_balance': asaas_balance,
            
            # Gráfico
            'chart_labels': list(chart_data.keys()),
            'chart_values': list(chart_data.values()),
        }
        return render(request, 'shop/dashboard.html', context)

class UpdateOrderStatusView(LoginRequiredMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not self.check_permission(request.user, order.product):
            messages.error(request, "Sem permissão.")
            return redirect('/')
            
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Status do pedido atualizado.")
            
        return redirect(request.META.get('HTTP_REFERER', '/'))

    def check_permission(self, user, product):
        if isinstance(product.provider, Artista):
            return product.provider.user == user
        elif isinstance(product.provider, Grupo):
            return product.provider.membros.filter(perfil=user.perfil, position__position__iexact='Líder').exists()
        return False

class UpdateBookingStatusView(LoginRequiredMixin, View):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        if not self.check_permission(request.user, booking.service):
            messages.error(request, "Sem permissão.")
            return redirect('/')
            
        new_status = request.POST.get('status')
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, f"Status do agendamento atualizado.")
            
        return redirect(request.META.get('HTTP_REFERER', '/'))

    def check_permission(self, user, service):
        if isinstance(service.provider, Artista):
            return service.provider.user == user
        elif isinstance(service.provider, Grupo):
            return service.provider.membros.filter(perfil=user.perfil, position__position__iexact='Líder').exists()
        return False

class CalculateShippingView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        payment_method = request.POST.get('payment_method', 'PIX')
        installments = int(request.POST.get('installments', 1))
        
        address_selector = request.POST.get('address_selector')
        pickup_on_site = address_selector == 'pickup'
        
        shipping_cost = Decimal('0.00')
        seller = product.seller
        
        if not pickup_on_site and address_selector and address_selector != 'pickup':
            address = get_object_or_404(request.user.addresses, id=address_selector)
            if seller.address and address and seller.address.latitude and seller.address.longitude and address.latitude and address.longitude:
                dist = haversine_distance(
                    seller.address.latitude, seller.address.longitude,
                    address.latitude, address.longitude
                )
                
                if Decimal(str(dist)) > seller.free_shipping_threshold_km:
                    shipping_cost = (Decimal(str(dist)) * seller.shipping_cost_per_km).quantize(Decimal('0.01'))
        
        subtotal = product.price * quantity
        base_total = subtotal + shipping_cost
        total_price = base_total
        
        if payment_method == 'CREDIT_CARD':
            total_price = calculate_gross_up_credit_card(total_price, installments)
        elif payment_method == 'PIX':
            total_price = calculate_gross_up_pix(total_price)
        
        payment_fee = total_price - base_total
        
        context = {
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'payment_fee': payment_fee,
            'total_price': total_price,
            'pickup_on_site': pickup_on_site,
        }
        return render(request, 'shop/partials/price_summary.html', context)

class CalculatePriceView(View):
    def get(self, request):
        print("calculando preço")
        item_type = request.GET.get('item_type')
        item_id = request.GET.get('item_id')
        payment_method = request.GET.get('payment_method', 'PIX')
        installments = int(request.GET.get('installments', 1))
        quantity = int(request.GET.get('quantity', 1))
        shipping_cost_raw = request.GET.get('shipping_cost', '0.00')
        # Limpar o valor: remover 'R$', espaços e trocar vírgula por ponto
        shipping_cost_raw = shipping_cost_raw.replace('R$', '').replace(' ', '').replace(',', '.')
        try:
            shipping_cost = Decimal(shipping_cost_raw)
        except:
            shipping_cost = Decimal('0.00')
        print(payment_method, installments)
        if not item_id:
            print("sem item")
            return HttpResponse("")

        if item_type == 'product':
            print("produto")
            item = get_object_or_404(Product, id=item_id)
            subtotal = item.price * quantity
        else:
            print("serviço")
            item = get_object_or_404(Service, id=item_id)
            subtotal = item.price
            
        base_total = subtotal + shipping_cost
        total_price = base_total
        
        if payment_method == 'CREDIT_CARD':
            total_price = calculate_gross_up_credit_card(total_price, installments)
        elif payment_method == 'PIX':
            total_price = calculate_gross_up_pix(total_price)
            
        payment_fee = total_price - base_total

        context = {
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'payment_fee': payment_fee,
            'total_price': total_price,
            'pickup_on_site': shipping_cost == 0
        }
        return render(request, 'shop/partials/price_summary.html', context)
