from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wishlist, WishlistItem
from .serializers import WishlistSerializer, WishlistItemSerializer
from products.models import Product


class WishlistView(generics.RetrieveAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist


class WishlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistItemSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist.items.select_related('product', 'product__category').prefetch_related('product__images')

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        if not product_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'product_id': 'This field is required.'})
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        product = Product.objects.get(id=product_id)
        item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
        if created:
            serializer = self.get_serializer(item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Product already in wishlist.'}, status=status.HTTP_400_BAD_REQUEST)
