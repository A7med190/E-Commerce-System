from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseModel


class Review(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], db_index=True)
    comment = models.TextField()
    is_verified = models.BooleanField(default=False, db_index=True, help_text='Verified purchase')
    is_approved = models.BooleanField(default=True, db_index=True)
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved', 'is_verified', '-rating']),
            models.Index(fields=['user', 'is_approved']),
            models.Index(fields=['is_approved', '-created_at']),
            models.Index(fields=['rating', 'is_approved']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.product.name} ({self.rating}/5)'


class ReviewImage(BaseModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/')
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']
        indexes = [
            models.Index(fields=['review', 'display_order']),
        ]

    def __str__(self):
        return f'Image for review {self.review.id}'
