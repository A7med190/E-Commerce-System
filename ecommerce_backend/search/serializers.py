from rest_framework import serializers
from products.serializers import ProductListSerializer


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=200)
    category = serializers.CharField(required=False, allow_blank=True, max_length=100)
    min_price = serializers.DecimalField(
        required=False, 
        max_digits=10, 
        decimal_places=2,
        min_value=0
    )
    max_price = serializers.DecimalField(
        required=False, 
        max_digits=10, 
        decimal_places=2,
        min_value=0
    )
    sort = serializers.ChoiceField(
        choices=[
            ('price_asc', 'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('name_asc', 'Name: A to Z'),
            ('name_desc', 'Name: Z to A'),
            ('rating', 'Highest Rated'),
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
        ],
        default='newest',
        required=False
    )
    page = serializers.IntegerField(default=1, min_value=1, required=False)
    page_size = serializers.IntegerField(default=20, min_value=1, max_value=100, required=False)


class SearchResultSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True)
    next = serializers.URLField(read_only=True, allow_null=True)
    previous = serializers.URLField(read_only=True, allow_null=True)
    page = serializers.IntegerField(read_only=True)
    page_size = serializers.IntegerField(read_only=True)
    total_pages = serializers.IntegerField(read_only=True)
    results = ProductListSerializer(many=True, read_only=True)


class SearchSuggestionSerializer(serializers.Serializer):
    suggestions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    total = serializers.IntegerField(read_only=True)
