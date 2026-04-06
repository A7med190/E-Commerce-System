from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderStatusHistory


@receiver(post_save, sender=Order)
def create_order_status_history(sender, instance, created, **kwargs):
    if created:
        OrderStatusHistory.objects.create(
            order=instance,
            status=instance.status,
            notes='Order created',
        )
