from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('add-product/<str:seller_type>/<uuid:seller_id>/', views.ProductCreateView.as_view(), name='product_create'),
    path('service-settings/<str:seller_type>/<uuid:seller_id>/', views.ServiceSettingsView.as_view(), name='service_settings'),
    path('product/<uuid:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/edit/<uuid:pk>/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('product/delete/<uuid:pk>/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('service/<uuid:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('service/edit/<uuid:pk>/', views.ServiceUpdateView.as_view(), name='service_edit'),
    path('service/delete/<uuid:pk>/', views.ServiceDeleteView.as_view(), name='service_delete'),
    path('buy/<uuid:product_id>/', views.ProcessPurchaseView.as_view(), name='process_purchase'),
    path('book/<uuid:service_id>/', views.ProcessBookingView.as_view(), name='process_booking'),
    path('available-slots/<uuid:service_id>/', views.GetAvailableSlotsView.as_view(), name='available_slots'),
    path('dashboard/<str:seller_type>/<uuid:seller_id>/', views.SalesDashboardView.as_view(), name='dashboard'),
    path('order/update-status/<uuid:order_id>/', views.UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('booking/update-status/<uuid:booking_id>/', views.UpdateBookingStatusView.as_view(), name='update_booking_status'),
    path('calculate-shipping/<uuid:product_id>/', views.CalculateShippingView.as_view(), name='calculate_shipping'),
    path('calculate-price/', views.CalculatePriceView.as_view(), name='calculate_price'),
]
