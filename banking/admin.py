from django.contrib import admin
from .models import BankAccount

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'account_number', 'document_name', 'owner', 'is_main')
    list_filter = ('bank_name', 'is_main')
    search_fields = ('document_name', 'document_number', 'account_number')
