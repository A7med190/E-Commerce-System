from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.db.models import Q
from products.models import Product
from products.serializers import ProductListSerializer


class SearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        category = request.query_params.get('category', '')
        min_price = request.query_params.get('min_price', '')
        max_price = request.query_params.get('max_price', '')
        sort = request.query_params.get('sort', '-created_at')

        qs = Product.objects.filter(is_active=True).select_related('category', 'inventory').prefetch_related('images')

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q))
        if category:
            qs = qs.filter(category__slug=category)
        if min_price:
            qs = qs.filter(base_price__gte=min_price)
        if max_price:
            qs = qs.filter(base_price__lte=max_price)

        sort_map = {
            'price_asc': 'base_price',
            'price_desc': '-base_price',
            'name_asc': 'name',
            'name_desc': '-name',
            'rating': '-average_rating',
            'newest': '-created_at',
            'oldest': 'created_at',
        }
        qs = qs.order_by(sort_map.get(sort, '-created_at'))

        from core.pagination import StandardPagination
        paginator = StandardPagination()
        result = paginator.paginate_queryset(qs, request)
        serializer = ProductListSerializer(result, many=True)
        return paginator.get_paginated_response(serializer.data)


class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        purchased_products = set()
        for order in user.orders.filter(status__in=['delivered', 'shipped', 'confirmed', 'processing']).prefetch_related('items'):
            for item in order.items.all():
                if item.product:
                    purchased_products.add(item.product.id)

        if not purchased_products:
            recommended = Product.objects.filter(is_active=True, is_featured=True)[:10]
            serializer = ProductListSerializer(recommended, many=True)
            return Response(serializer.data)

        co_purchased = {}
        for order in user.orders.filter(status__in=['delivered', 'shipped', 'confirmed', 'processing']).prefetch_related('items__product'):
            for item in order.items.all():
                if item.product and item.product.id not in purchased_products:
                    co_purchased[item.product.id] = co_purchased.get(item.product.id, 0) + 1

        top_product_ids = sorted(co_purchased.keys(), key=lambda x: co_purchased[x], reverse=True)[:10]
        recommended = Product.objects.filter(id__in=top_product_ids, is_active=True).select_related('category', 'inventory').prefetch_related('images')
        recommended = sorted(recommended, key=lambda p: co_purchased.get(p.id, 0), reverse=True)

        serializer = ProductListSerializer(recommended, many=True)
        return Response(serializer.data)
