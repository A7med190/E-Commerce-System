from rest_framework import serializers
from .models import Review, ReviewImage


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image']


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_email', 'product', 'rating', 'comment', 'is_verified', 'is_approved', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_email', 'is_verified', 'is_approved', 'created_at', 'updated_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required=False, write_only=True)

    class Meta:
        model = Review
        fields = ['product', 'rating', 'comment', 'images']

    def validate_product(self, value):
        user = self.context['request'].user
        if Review.objects.filter(user=user, product=value).exists():
            raise serializers.ValidationError('You have already reviewed this product.')
        has_purchased = user.orders.filter(status__in=['delivered', 'shipped'], items__product=value).exists()
        self._has_purchased = has_purchased
        return value

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        review = Review.objects.create(
            user=self.context['request'].user,
            is_verified=getattr(self, '_has_purchased', False),
            **validated_data,
        )
        for image in images:
            ReviewImage.objects.create(review=review, image=image)
        return review
