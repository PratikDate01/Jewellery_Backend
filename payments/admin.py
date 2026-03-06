from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'transaction_id', 'payment_method', 'amount', 'status', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['transaction_id', 'user__email', 'order__id']
    readonly_fields = ['created_at', 'updated_at']
