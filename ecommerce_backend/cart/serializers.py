from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product, CustomizationValue
from products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source='product', write_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'customizations', 'price_at_add', 'total_price']
        read_only_fields = ['id', 'price_at_add']


class CartItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True), source='product', write_only=True)
    customizations = serializers.JSONField(required=False, default=list)

    class Meta:
        model = CartItem
        fields = ['product_id', 'quantity', 'customizations']

    def validate(self, attrs):
        product = attrs['product']
        customizations = attrs.get('customizations', [])
        inventory = getattr(product, 'inventory', None)
        if not inventory or not inventory.is_in_stock:
            raise serializers.ValidationError({'product': 'Product is out of stock.'})
        if attrs.get('quantity', 1) > inventory.stock_quantity:
            raise serializers.ValidationError({'quantity': f'Only {inventory.stock_quantity} items in stock.'})
        for cust in customizations:
            if 'option_id' not in cust:
                raise serializers.ValidationError({'customizations': 'Each customization must have an option_id.'})
        return attrs

    def create(self, validated_data):
        cart, _ = Cart.objects.get_or_create(user=self.context['request'].user)
        product = validated_data['product']
        customizations = validated_data.get('customizations', [])
        price = self._calculate_price(product, customizations)
        validated_data['price_at_add'] = price
        validated_data['cart'] = cart
        return super().create(validated_data)

    def _calculate_price(self, product, customizations):
        base_price = product.base_price
        value_ids = []
        for cust in customizations:
            vids = cust.get('value_ids', [])
            if isinstance(vids, list):
                value_ids.extend(vids)
            elif cust.get('value_id'):
                value_ids.append(cust['value_id'])
        if value_ids:
            values = CustomizationValue.objects.filter(id__in=value_ids)
            from decimal import Decimal
            total_modifier = Decimal('0')
            for value in values:
                if value.modifier_type == 'fixed':
                    total_modifier += value.price_modifier
                elif value.modifier_type == 'percent':
                    total_modifier += base_price * (value.price_modifier / Decimal('100'))
            return base_price + total_modifier
        return base_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
