import logging
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def setup_signals():
    from products.models import Inventory, Product
    from orders.models import Order
    from reviews.models import Review
    from users.models import User
    
    @receiver(post_save, sender=Inventory)
    def inventory_post_save(sender, instance, created, **kwargs):
        if instance.is_low_stock:
            from core.services.business import NotificationService
            NotificationService.send_low_stock_alert(instance.product, instance.stock_quantity)
        
        cache_key = f"inventory:{instance.product_id}"
        from django.core.cache import cache
        cache.delete(cache_key)
        
        logger.debug(f"Inventory updated for product {instance.product_id}: {instance.stock_quantity}")

    @receiver(post_delete, sender=Inventory)
    def inventory_post_delete(sender, instance, **kwargs):
        cache_key = f"inventory:{instance.product_id}"
        from django.core.cache import cache
        cache.delete(cache_key)

    @receiver(post_save, sender=Order)
    def order_post_save(sender, instance, created, **kwargs):
        from core.services.business import NotificationService
        if instance.user:
            NotificationService.send_order_confirmation(instance)
        
        from core.outbox import outbox_service
        outbox_service.publish(
            'order.created' if created else 'order.updated',
            {
                'order_id': str(instance.id),
                'order_number': instance.order_number,
                'user_id': str(instance.user_id) if instance.user else None,
                'status': instance.status,
                'total': str(instance.total),
                'created': created,
            }
        )

    @receiver(pre_delete, sender=Order)
    def order_pre_delete(sender, instance, **kwargs):
        logger.warning(f"Order {instance.order_number} is being deleted")
        
        from core.outbox import outbox_service
        outbox_service.publish(
            'order.deleted',
            {
                'order_id': str(instance.id),
                'order_number': instance.order_number,
            }
        )

    @receiver(post_save, sender=Review)
    def review_post_save(sender, instance, created, **kwargs):
        if instance.is_approved and instance.is_verified:
            from django.core.cache import cache
            cache.delete(f"product_rating:{instance.product_id}")
            
            from core.webhooks import channel_manager
            import asyncio
            try:
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(channel_manager.broadcast_to_group(
                        f"product_{instance.product_id}",
                        'product_rating_update',
                        {'product_id': str(instance.product_id)}
                    ))
            except Exception:
                pass

    @receiver(post_save, sender=User)
    def user_post_save(sender, instance, created, **kwargs):
        if created:
            from core.outbox import outbox_service
            outbox_service.publish(
                'user.created',
                {
                    'user_id': str(instance.id),
                    'email': instance.email,
                    'created_at': instance.created_at.isoformat(),
                }
            )

    @receiver(post_save, sender=Product)
    def product_post_save(sender, instance, created, **kwargs):
        from django.core.cache import cache
        cache.delete(f"product:{instance.slug}")
        
        if not created and not instance.is_active:
            from core.outbox import outbox_service
            outbox_service.publish(
                'product.deactivated',
                {
                    'product_id': str(instance.id),
                    'sku': instance.sku,
                }
            )

    logger.info("All signals registered successfully")


import django
from django.apps import apps

if apps.ready:
    setup_signals()
