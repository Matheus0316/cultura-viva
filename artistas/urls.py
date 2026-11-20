from django.urls import path
from .views import (
    ArtistaListView, ArtistaDetailView, ArtistaRequestView, ArtistaDashboardView, ArtistaPostCreateView, ArtistaUpdateView,
    ArtistaEventCreateView, FollowArtistaView,
    AdminArtistRequestListView, AdminApproveRequestView, AdminRejectRequestView,
    ArtistaAddressUpdateView, ArtistaDeliveryUpdateView
)

app_name = 'artistas'

urlpatterns = [
    path('', ArtistaListView.as_view(), name='artista_list'),
    path('cadastro/', ArtistaRequestView.as_view(), name='artista_request'),
    path('painel/', ArtistaDashboardView.as_view(), name='artista_dashboard'),
    path('painel/novo-post/', ArtistaPostCreateView.as_view(), name='artista_post_create'),
    path('painel/novo-evento/', ArtistaEventCreateView.as_view(), name='artista_event_create'),
    path('painel/endereco/', ArtistaAddressUpdateView.as_view(), name='artista_address_edit'),
    path('painel/entrega/', ArtistaDeliveryUpdateView.as_view(), name='artista_delivery_edit'),

    # Admin Requests
    path('solicitacoes/', AdminArtistRequestListView.as_view(), name='admin_request_list'),
    path('solicitacoes/<uuid:pk>/aprovar/', AdminApproveRequestView.as_view(), name='admin_approve_request'),
    path('solicitacoes/<uuid:pk>/rejeitar/', AdminRejectRequestView.as_view(), name='admin_reject_request'),

    path('<uuid:pk>/', ArtistaDetailView.as_view(), name='artista_detail'),
    path('<uuid:pk>/editar/', ArtistaUpdateView.as_view(), name='artista_edit'),
    path('<uuid:pk>/seguir/', FollowArtistaView.as_view(), name='follow_artista'),
]
