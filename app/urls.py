"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    path('artistas/', include('artistas.urls')),
    path('acervo/', include('acervo.urls')),
    path('grupos/', include('grupos.urls')), # Agora focado em Projetos Sociais
    path('publicações/', include('post.urls')), # Mantido para notícias/blog geral
    path('perfil/', include('perfil.urls')),
    path('comments/', include('comments.urls')),
    path('events/', include('events.urls')),
    path('team/', include('team.urls')),
    path('loja/', include('shop.urls')),
    path('pagamentos/', include('payments.urls')),
    path('banking/', include('banking.urls')),
    path('api/webhook/asaas/', include('payments.urls_webhook')),
    path('', include('home.urls')),

    path('summernote/', include('django_summernote.urls')),
]
if settings.DEBUG:
    # Rota para arquivos de MÍDIA (uploads de usuários)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Rota para arquivos ESTÁTICOS (CSS, JS, imagens do CKEditor)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
