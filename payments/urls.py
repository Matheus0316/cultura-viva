from django.urls import path
from .views import PaymentDetailView

app_name = 'payments'

urlpatterns = [
    path('<uuid:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
]
