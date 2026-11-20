from django.urls import path
from .views import (
    SeguirGrupoView, DeixarDeSeguirGrupoView, ProfileListView, ProfileDetailVeiw,
    UpdateMembershipView, RemoverMembroView, ProfileEditView,
    UserListView, PromoteSuperuserView, CreateArtistFromAdminView, RemoveArtistView, ToggleAcervoPermissionView,
    AddressListView, AddressCreateView, AddressUpdateView, AddressDeleteView
)
app_name = 'perfil'

urlpatterns = [
    path('seguir/<uuid:grupo_id>', SeguirGrupoView.as_view(), name='seguir_grupo'),
    path('deixar_de_seguir/<uuid:grupo_id>', DeixarDeSeguirGrupoView.as_view(), name='deixar_De_seguir_grupo'),
    path('<uuid:grupo_id>', ProfileListView.as_view(), name='profile_list'),
    path('detail/<uuid:id>', ProfileDetailVeiw.as_view(), name='profile_detail'),
    path('edit/<uuid:id>', ProfileEditView.as_view(), name='profile_edit'),
    path('atualizar_cargo/<uuid:perfil_id>', UpdateMembershipView.as_view(), name='update_membership'),
    path('remover_membro/<uuid:perfil_id>', RemoverMembroView.as_view(), name='remove_member'),

    # Admin Management
    path('manage/', UserListView.as_view(), name='user_list'),
    path('manage/<int:user_id>/promote/', PromoteSuperuserView.as_view(), name='promote_superuser'),
    path('manage/<int:user_id>/make-artist/', CreateArtistFromAdminView.as_view(), name='create_artist_from_admin'),
    path('manage/<int:user_id>/remove-artist/', RemoveArtistView.as_view(), name='remove_artist_from_admin'),
    path('manage/<int:user_id>/toggle-acervo/', ToggleAcervoPermissionView.as_view(), name='toggle_acervo_permission'),

    # Address Management
    path('addresses/', AddressListView.as_view(), name='address_list'),
    path('address/add/', AddressCreateView.as_view(), name='address_add'),
    path('address/<uuid:pk>/edit/', AddressUpdateView.as_view(), name='address_edit'),
    path('address/<uuid:pk>/delete/', AddressDeleteView.as_view(), name='address_delete'),
]
