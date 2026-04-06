from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer, CartItemCreateSerializer


class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def delete(self, request):
        cart = self.get_object()
        cart.clear()
        return Response({'detail': 'Cart cleared.'}, status=status.HTTP_200_OK)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart.items.select_related('product', 'product__category').prefetch_related('product__images')

    def get_serializer_class(self):
        if self.action == 'create':
            return CartItemCreateSerializer
        return CartItemSerializer

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product = serializer.validated_data['product']
        customizations = serializer.validated_data.get('customizations', [])
        existing = cart.items.filter(product=product, customizations=customizations).first()
        if existing:
            existing.quantity += serializer.validated_data.get('quantity', 1)
            existing.save()
            self._instance = existing
        else:
            self._instance = serializer.save(cart=cart)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = getattr(self, '_instance', serializer.instance)
        output_serializer = CartItemSerializer(instance)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        instance.delete()
