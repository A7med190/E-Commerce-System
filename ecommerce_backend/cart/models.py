from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel


class Cart(BaseModel):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='cart')

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Cart for {self.user.email}'

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def clear(self):
        self.items.all().delete()


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1)
    customizations = models.JSONField(default=list, help_text='List of {option_id, value_id(s), text_value}')
    price_at_add = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def total_price(self):
        return self.price_at_add * self.quantity
