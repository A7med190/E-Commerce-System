from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'method', 'status', 'paid_at', 'created_at']
    list_filter = ['method', 'status']
    search_fields = ['order__order_number', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_charge_id', 'paid_at']
