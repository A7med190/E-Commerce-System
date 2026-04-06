from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Review, ReviewImage
from .serializers import ReviewSerializer, ReviewCreateSerializer
from core.permissions import IsAdmin, IsOwnerOrReadOnly


class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        qs = Review.objects.filter(is_approved=True).select_related('user', 'product').prefetch_related('images')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.kwargs.get('product_id'):
            from products.models import Product
            context['product'] = Product.objects.get(id=self.kwargs['product_id'])
        return context

    def perform_create(self, serializer):
        product = self.get_serializer_context().get('product')
        if product:
            serializer.save(product=product)
        else:
            serializer.save()


class ReviewModerateView(generics.GenericAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdmin]
    queryset = Review.objects.all()

    def patch(self, request, pk):
        review = self.get_object()
        is_approved = request.data.get('is_approved', review.is_approved)
        review.is_approved = is_approved
        review.save()
        return Response(ReviewSerializer(review).data)
