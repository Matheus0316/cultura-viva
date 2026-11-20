from django.urls import path
from .views import ParocoView

app_name = 'team'

urlpatterns = [
    path('paroco/', ParocoView.as_view(), name='paroco'),
    #path('paroco/<uuid:id>/', ParocoView.as_view(), name='member_edit'),
    path('paroco/', ParocoView.as_view(), name='member_delete'),
]
