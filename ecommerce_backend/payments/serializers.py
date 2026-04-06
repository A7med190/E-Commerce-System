from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'order', 'order_number', 'amount', 'currency', 'method', 'status', 'stripe_payment_intent_id', 'paid_at', 'created_at']
        read_only_fields = ['id', 'order', 'order_number', 'stripe_payment_intent_id', 'paid_at', 'created_at']


class PaymentIntentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()

    def validate_order_id(self, value):
        from orders.models import Order
        user = self.context['request'].user
        try:
            order = Order.objects.get(id=value, user=user, status='pending')
        except Order.DoesNotExist:
            raise serializers.ValidationError('Order not found or not in pending status.')
        return order
