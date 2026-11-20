from django.urls import path
from . import views
from .views import GrupoListView, GrupoDetailView, GrupoCreateView, GrupoEditView, GrupoDeleteView

app_name = 'grupos'

urlpatterns = [
    path('', GrupoListView.as_view(), name='grupo_list'),
    path('create/', GrupoCreateView.as_view(), name='grupo_create'),
    path('<uuid:id>/', GrupoDetailView.as_view(), name='grupo_detail'),
    path('<uuid:id>/edit/', GrupoEditView.as_view(), name='grupo_edit'),
    path('<uuid:id>/delete/', GrupoDeleteView.as_view(), name='grupo_delete'),
    path('<uuid:id>/endereco/', views.GrupoAddressUpdateView.as_view(), name='grupo_address_edit'),
    path('<uuid:id>/entrega/', views.GrupoDeliveryUpdateView.as_view(), name='grupo_delivery_edit'),
    
    # Admin Approval
    path('admin/approve/<uuid:pk>/', views.AdminApproveGrupoRequestView.as_view(), name='admin_approve_request'),
    path('admin/reject/<uuid:pk>/', views.AdminRejectGrupoRequestView.as_view(), name='admin_reject_request'),
]
