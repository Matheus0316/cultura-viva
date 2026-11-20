from django.urls import path
from .views import IndexView, LoginView, LogoutView, RegisterView, SendChangePasswordEmailView, ChangePasswordView, ParocoView

app_name = 'home'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('send-change-password-email/', SendChangePasswordEmailView.as_view(), name='send_change_password_email'),
    path('change-password/<uuid:token>/', ChangePasswordView.as_view(), name='change_password'),
    path('paroco/', ParocoView.as_view(), name="paroco")
]
