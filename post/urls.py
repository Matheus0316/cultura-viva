from django.urls import path
from .views import PostCreateView, PostDetailView, PostEditView, postDeleteView, AcervoListView

app_name = 'post'

urlpatterns = [
    path('<uuid:group_token>/new_post/', PostCreateView.as_view(), name='post_create'),
    path('acervo/', AcervoListView.as_view(), name='acervo_list'),
    path('<uuid:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('editar/<uuid:post_id>/', PostEditView.as_view(), name='edit_post'),
    path('deletar/<uuid:post_id>/', postDeleteView.as_view(), name='post_delete'),
]
