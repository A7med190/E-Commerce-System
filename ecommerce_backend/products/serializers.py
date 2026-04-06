from rest_framework import serializers
from .models import Category, Product, ProductImage, CustomizationOption, CustomizationValue, ProductCustomization, Inventory


class CustomizationValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationValue
        fields = ['id', 'value', 'price_modifier', 'modifier_type', 'is_default', 'display_order']


class CustomizationOptionSerializer(serializers.ModelSerializer):
    values = CustomizationValueSerializer(many=True, read_only=True)

    class Meta:
        model = CustomizationOption
        fields = ['id', 'name', 'option_type', 'is_required', 'display_order', 'values']


class ProductCustomizationSerializer(serializers.ModelSerializer):
    option = CustomizationOptionSerializer(read_only=True)
    option_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomizationOption.objects.all(), source='option', write_only=True
    )

    class Meta:
        model = ProductCustomization
        fields = ['id', 'product', 'option', 'option_id', 'is_required_override', 'min_value', 'max_value', 'is_required']
        read_only_fields = ['id', 'product', 'is_required']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'display_order']


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'base_price', 'sku', 'category', 'category_name', 'is_active', 'is_featured', 'average_rating', 'review_count', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'base_price', 'sku', 'category', 'category_name', 'is_active', 'is_featured', 'images', 'average_rating', 'review_count', 'in_stock', 'created_at', 'updated_at']

    def get_in_stock(self, obj):
        inventory = getattr(obj, 'inventory', None)
        return inventory.is_in_stock if inventory else False


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'slug', 'description', 'base_price', 'sku', 'category', 'is_active', 'is_featured']


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 'image', 'is_active', 'children', 'product_count']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'product', 'product_name', 'stock_quantity', 'low_stock_threshold', 'is_in_stock', 'is_low_stock']
        read_only_fields = ['id', 'product', 'is_in_stock', 'is_low_stock']


class InventoryUpdateSerializer(serializers.Serializer):
    stock_quantity = serializers.IntegerField(min_value=0)
    low_stock_threshold = serializers.IntegerField(min_value=0, required=False)
