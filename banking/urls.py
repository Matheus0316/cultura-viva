from django.urls import path
from . import views

app_name = 'banking'

urlpatterns = [
    path('update/<str:seller_type>/<uuid:seller_id>/', views.UpdateBankAccountView.as_view(), name='update_bank_account'),
    path('form/<str:seller_type>/<uuid:seller_id>/', views.BankAccountFormView.as_view(), name='bank_account_form'),
    path('info/<str:seller_type>/<uuid:seller_id>/', views.BankAccountInfoView.as_view(), name='bank_account_info'),
]
