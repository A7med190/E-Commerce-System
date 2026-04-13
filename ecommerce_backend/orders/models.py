from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel


class Order(BaseModel):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='orders', db_index=True)
    order_number = models.CharField(max_length=50, unique=True, editable=False, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_index=True)
    shipping_address = models.JSONField()
    billing_address = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['total', '-created_at']),
            models.Index(fields=['order_number']),
        ]

    def __str__(self):
        return f'{self.order_number} - {self.user.email if self.user else "Guest"}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            from core.utils import generate_order_number
            self.order_number = generate_order_number()
        self.total = self.subtotal + self.tax + self.shipping_cost
        super().save(*args, **kwargs)


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, db_index=True)
    product_name = models.CharField(max_length=300)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    customizations = models.JSONField(default=list)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['order', 'id']),
        ]

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'


class OrderStatusHistory(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', '-created_at']),
        ]

    def __str__(self):
        return f'{self.order.order_number} -> {self.status}'
