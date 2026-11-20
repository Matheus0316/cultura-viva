from django.urls import path
from .views import AcervoListView, AcervoDetailView, AcervoCreateView, AcervoUpdateView, AcervoDeleteView

app_name = 'acervo'

urlpatterns = [
    path('', AcervoListView.as_view(), name='acervo_list'),
    path('novo/', AcervoCreateView.as_view(), name='acervo_create'),
    path('<uuid:pk>/', AcervoDetailView.as_view(), name='acervo_detail'),
    path('<uuid:pk>/editar/', AcervoUpdateView.as_view(), name='acervo_update'),
    path('<uuid:pk>/remover/', AcervoDeleteView.as_view(), name='acervo_delete'),
]
