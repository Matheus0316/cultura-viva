from django.shortcuts import render
from django.views import View
from .models import Member

class ParocoView(View):
    def get(self, request):
        paroco = Member.objects.filter(active=True, position__name='Paroco').first()
        context = {
            'paroco':paroco
        }
        return render(request, 'team/paroco.html', context)
