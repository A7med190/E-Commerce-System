from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product, ProductImage, CustomizationOption, CustomizationValue, ProductCustomization, Inventory
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ProductImageSerializer, CustomizationOptionSerializer,
    ProductCustomizationSerializer, InventorySerializer, InventoryUpdateSerializer,
)
from .filters import ProductFilter
from core.permissions import IsAdmin


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        qs = super().get_queryset()
        parent = self.request.query_params.get('parent', None)
        if parent == 'null':
            return qs.filter(parent__isnull=True)
        if parent:
            return qs.filter(parent_id=parent)
        return qs


class ProductViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['name', 'base_price', 'created_at', 'average_rating']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('category', 'inventory').prefetch_related('images', 'product_customizations__option')
        category = self.request.query_params.get('category', None)
        if category:
            qs = qs.filter(category__slug=category)
        is_featured = self.request.query_params.get('featured', None)
        if is_featured == 'true':
            qs = qs.filter(is_featured=True)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            qs = qs.filter(base_price__gte=min_price)
        if max_price:
            qs = qs.filter(base_price__lte=max_price)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [permissions.AllowAny()]

    @action(detail=True, methods=['get'])
    def customizations(self, request, slug=None):
        product = self.get_object()
        customizations = product.product_customizations.select_related('option').prefetch_related('option__values')
        serializer = ProductCustomizationSerializer(customizations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        product = self.get_object()
        related = Product.objects.filter(
            category=product.category, is_active=True
        ).exclude(id=product.id)[:8]
        serializer = ProductListSerializer(related, many=True)
        return Response(serializer.data)


class ProductCustomizationManageView(generics.ListCreateAPIView):
    serializer_class = ProductCustomizationSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return ProductCustomization.objects.filter(product_id=product_id).select_related('option').prefetch_related('option__values')

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        serializer.save(product=product)


class InventoryViewSet(viewsets.ModelViewSet):
    serializer_class = InventorySerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Inventory.objects.select_related('product')

    @action(detail=True, methods=['patch'])
    def update_stock(self, request, pk=None):
        inventory = self.get_object()
        serializer = InventoryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory.stock_quantity = serializer.validated_data['stock_quantity']
        if 'low_stock_threshold' in serializer.validated_data:
            inventory.low_stock_threshold = serializer.validated_data['low_stock_threshold']
        inventory.save()
        return Response(InventorySerializer(inventory).data)
