from django.db import models
from core.models import BaseModel


class Wishlist(BaseModel):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='wishlist')

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f'Wishlist for {self.user.email}'


class WishlistItem(BaseModel):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, db_index=True)

    class Meta:
        unique_together = ('wishlist', 'product')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wishlist', '-created_at']),
            models.Index(fields=['product', '-created_at']),
        ]

    def __str__(self):
        return f'{self.product.name} in {self.wishlist.user.email}'
