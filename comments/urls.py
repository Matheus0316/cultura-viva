from django.urls import path
from .views import CommentCreateView

app_name = 'comments'

urlpatterns = [
    path('comment/<uuid:post_id>/', CommentCreateView.as_view(), name='comment_create'),
]
