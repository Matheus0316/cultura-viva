from django.contrib import admin
from .models import Product, Service, Booking, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'price', 'stock', 'is_active')
    list_filter = ('is_active', 'content_type')
    search_fields = ('name', 'description')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'price', 'duration_hours', 'is_active')
    list_filter = ('is_active', 'content_type')
    search_fields = ('name', 'description')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('service', 'client', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('service__name', 'client__username')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'buyer', 'quantity', 'total_price', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('product__name', 'buyer__username')
