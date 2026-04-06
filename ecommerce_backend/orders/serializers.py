from decimal import Decimal
from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'customizations', 'total']
        read_only_fields = ['id']


class OrderCreateSerializer(serializers.Serializer):
    shipping_address_id = serializers.UUIDField(required=True)
    billing_address_id = serializers.UUIDField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_shipping_address_id(self, value):
        from users.models import Address
        user = self.context['request'].user
        try:
            address = Address.objects.get(id=value, user=user)
        except Address.DoesNotExist:
            raise serializers.ValidationError('Shipping address not found.')
        return address

    def validate_billing_address_id(self, value):
        if value:
            from users.models import Address
            user = self.context['request'].user
            try:
                return Address.objects.get(id=value, user=user)
            except Address.DoesNotExist:
                raise serializers.ValidationError('Billing address not found.')
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        cart = user.cart
        if not cart.items.exists():
            raise serializers.ValidationError('Cart is empty.')

        shipping_address = validated_data['shipping_address_id']
        billing_address = validated_data.get('billing_address_id') or shipping_address

        shipping_addr_data = {
            'street': shipping_address.street,
            'city': shipping_address.city,
            'state': shipping_address.state,
            'zip_code': shipping_address.zip_code,
            'country': shipping_address.country,
        }
        billing_addr_data = {
            'street': billing_address.street,
            'city': billing_address.city,
            'state': billing_address.state,
            'zip_code': billing_address.zip_code,
            'country': billing_address.country,
        }

        order = Order.objects.create(
            user=user,
            shipping_address=shipping_addr_data,
            billing_address=billing_addr_data,
            notes=validated_data.get('notes', ''),
        )

        subtotal = Decimal('0')
        for cart_item in cart.items.all():
            item_total = cart_item.total_price
            subtotal += item_total
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.price_at_add,
                quantity=cart_item.quantity,
                customizations=cart_item.customizations,
                total=item_total,
            )

        order.subtotal = subtotal
        order.tax = subtotal * Decimal('0.10')
        order.shipping_cost = Decimal('9.99') if subtotal < Decimal('100') else Decimal('0')
        order.save()

        cart.clear()
        return order


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'subtotal', 'tax', 'shipping_cost', 'total', 'shipping_address', 'billing_address', 'notes', 'items', 'status_history', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_number', 'status', 'subtotal', 'tax', 'shipping_cost', 'total', 'shipping_address', 'billing_address', 'notes', 'items', 'status_history', 'created_at', 'updated_at']

    def get_status_history(self, obj):
        return [{'status': h.status, 'notes': h.notes, 'created_at': h.created_at} for h in obj.status_history.all()]


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s[0] for s in Order.STATUS_CHOICES])
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.save()
        OrderStatusHistory.objects.create(
            order=instance,
            status=validated_data['status'],
            notes=validated_data.get('notes', ''),
        )
        return instance
