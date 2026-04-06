from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseModel


class Review(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_verified = models.BooleanField(default=False, help_text='Verified purchase')
    is_approved = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.product.name} ({self.rating}/5)'


class ReviewImage(BaseModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/')

    def __str__(self):
        return f'Image for review {self.review.id}'
