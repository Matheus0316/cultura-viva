from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from .models import Event, EventReminder
from .forms import EventForm
from .tasks import send_email_remember_event
from datetime import timedelta
from app.celery import app as celery_app


class EventListView(View):
    def get(self, request):
        search = request.GET.get('search', '')
        filters_options = request.GET.getlist('filter')
        events = Event.objects.all().order_by('-created_at')

        if search:
            events = events.filter(title__icontains=search)

        time_filter = Q()
        if 'upcoming' in filters_options:
            time_filter |= Q(date__gte=timezone.now())
        if 'occurred' in filters_options:
            time_filter |= Q(date__lt=timezone.now())
        events = events.order_by('-created_at')

        status_filter = Q()
        if 'active' in filters_options:
            status_filter |= Q(active=True)
        if 'cancelled' in filters_options:
            status_filter |= Q(active=False)

        type_filter = Q()
        if 'artist_events' in filters_options:
            type_filter |= Q(artista__isnull=False)
        if 'city_events' in filters_options:
            type_filter |= Q(artista__isnull=True, grupo__isnull=True)
        if 'group_events' in filters_options:
            type_filter |= Q(grupo__isnull=False)

        if time_filter:
            events = events.filter(time_filter)
        if status_filter:
            events = events.filter(status_filter)
        if type_filter:
            events = events.filter(type_filter)

        events = events.order_by('-created_at')

        paginator = Paginator(events, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'events': page_obj,
            'search': search,
            'filter_options': filters_options
        }
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('events/partials/event_list.html', context)
            return JsonResponse({'html': html})
        return render(request, 'events/event_list.html', context)


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        # Verifica se o usuário é líder de pelo menos um grupo
        from grupos.models import Grupo
        return Grupo.objects.filter(
            membros__perfil=self.request.user.perfil,
            membros__position__position__iexact='Líder'
        ).exists()

    def get(self, request):
        initial = {}
        grupo_id = request.GET.get('grupo')
        if grupo_id:
            initial['grupo'] = grupo_id
        form = EventForm(request=request, initial=initial)
        context = {'form': form}
        return render(request, 'events/event_create.html', context)

    def post(self, request):
        form = EventForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento criado com sucesso!')
            return redirect('events:event_list')
        else:
            messages.error(request, 'Erro ao criar o evento. Verifique os dados e tente novamente.')
            context = {'form': form,}
            return render(request, 'events/event_create.html', context)

class EventDetailView(View):
    def get(self, request, id):
        event = get_object_or_404(Event, id=id)
        is_riminder = False
        if request.user.is_authenticated:
            is_riminder = EventReminder.objects.filter(event=event, profile=request.user.perfil).exists()
            
        context = {
            'event': event,
            'is_riminder': is_riminder
        }
        return render(request, 'events/event_detail.html', context)


class EventEditView(View):
    def get(self, request, id):
        event = get_object_or_404(Event, id=id)
        
        # Permissão: Superuser, Dono do Artista ou Líder do Grupo
        is_leader = False
        if event.grupo:
             is_leader = event.grupo.membros.filter(
                perfil=request.user.perfil,
                position__position__iexact='Líder'
            ).exists()

        if not request.user.is_superuser and (not event.artista or event.artista.user != request.user) and not is_leader:
            messages.error(request, 'Você não tem permissão para editar este evento.')
            return redirect('events:event_detail', id=event.id)
            
        form = EventForm(instance=event, request=request)
        context = {'form': form, 'event': event}
        
        if request.headers.get('HX-Request'):
            return render(request, 'events/partials/event_edit_modal.html', context)
        return render(request, 'events/event_edit.html', context)

    def post(self, request, id):
        event = get_object_or_404(Event, id=id)
        
        is_leader = False
        if event.grupo:
             is_leader = event.grupo.membros.filter(
                perfil=request.user.perfil,
                position__position__iexact='Líder'
            ).exists()

        if not request.user.is_superuser and (not event.artista or event.artista.user != request.user) and not is_leader:
            messages.error(request, 'Você não tem permissão para editar este evento.')
            return redirect('events:event_detail', id=event.id)

        form = EventForm(request.POST, request.FILES, instance=event, request=request)
        if form.is_valid():
            form.save()
            
            if request.headers.get('HX-Request'):
                from django.http import HttpResponse
                response = HttpResponse()
                response['HX-Refresh'] = 'true'
                return response
                
            messages.success(request, 'Evento atualizado com sucesso!')
            return redirect('events:event_detail', id=event.id)
        else:
            messages.error(request, 'Erro ao atualizar o evento. Verifique os dados e tente novamente.')
            context = {'form': form, 'event': event}
            if request.headers.get('HX-Request'):
                return render(request, 'events/partials/event_edit_modal.html', context)
            return render(request, 'events/event_edit.html', context)


class EventReminderView(View):
    def get(self, request, id):
        event = get_object_or_404(Event, id=id)
        time_reminder = event.date - timedelta(days=1)

        if timezone.now() >= time_reminder:
            messages.info(request, 'O evento está muito próximo para enviar um lembrete.')
        else:
            task = send_email_remember_event.apply_async(
                args=[request.user.email, request.user.perfil.id, event.id],
                eta=time_reminder
            )
            EventReminder.objects.create(
                event=event,
                profile=request.user.perfil,
                task_id=task.id
            )
            messages.success(request, 'Lembrete de evento agendado com sucesso! Você receberá um email um dia antes do evento.')
        return redirect('events:event_detail', id=event.id)

class EventDeleteView(View):
    def post(self, request, id):
        event = get_object_or_404(Event, id=id)
        
        # Permissão: Superuser, Dono do Artista ou Líder do Grupo
        is_leader = False
        if event.grupo:
             is_leader = event.grupo.membros.filter(
                perfil=request.user.perfil,
                position__position__iexact='Líder'
            ).exists()

        if not request.user.is_superuser and (not event.artista or event.artista.user != request.user) and not is_leader:
            return JsonResponse({'error': 'Você não tem permissão para excluir este evento.'}, status=403)
        reminders = EventReminder.objects.filter(event=event)
        for reminder in reminders:
            celery_app.control.revoke(reminder.task_id, terminate=True)
            reminder.delete()
            
        event.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
             return JsonResponse({'success': True})
        
        messages.success(request, 'Evento excluído com sucesso.')
        return redirect('events:event_list')

class EventRemoveReminderView(View):
    def get(self, request, id):
        event = get_object_or_404(Event, id=id)
        try:
            reminder = get_object_or_404(EventReminder, event=event, profile=request.user.perfil)
            celery_app.control.revoke(reminder.task_id, terminate=True)
            reminder.delete()
            messages.success(request, 'Lembrete de evento removido com sucesso!')
        except:
            messages.error(request, 'Nenhum lembrete encontrado para este evento.')
        return redirect('events:event_detail', id=event.id)
