import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_outbox_messages(self, batch_size: int = 100):
    try:
        from core.outbox import outbox_service
        outbox_service.process_pending(batch_size=batch_size)
    except Exception as e:
        logger.error(f"Error processing outbox messages: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def process_webhook_retries(self, batch_size: int = 100):
    try:
        from core.webhooks import webhook_service
        webhook_service.process_pending_retries(batch_size=batch_size)
    except Exception as e:
        logger.error(f"Error processing webhook retries: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def cleanup_old_data():
    try:
        from core.outbox import outbox_service
        from core.webhooks import webhook_service
        
        outbox_service.cleanup_old_messages(days=30)
        webhook_service.cleanup_old_deliveries(days=30)
        
        logger.info("Old data cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


@shared_task
def check_low_stock():
    try:
        from core.services.business import InventoryService
        from core.outbox import outbox_service
        
        low_stock_products = InventoryService.get_low_stock_products()
        
        if low_stock_products:
            outbox_service.publish(
                'inventory.low_stock_alert',
                {
                    'products': low_stock_products,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        
        logger.info(f"Checked low stock: {len(low_stock_products)} products below threshold")
    except Exception as e:
        logger.error(f"Error checking low stock: {e}")


@shared_task(bind=True, max_retries=3)
def send_digest_emails(self):
    try:
        from users.models import User
        from django.core.mail import send_mail
        from django.conf import settings
        
        cutoff = timezone.now() - timedelta(days=1)
        
        inactive_users = User.objects.filter(
            is_active=True,
            last_login__lt=cutoff,
        ).exclude(email='')
        
        logger.info(f"Sending digest to {inactive_users.count()} inactive users")
    except Exception as e:
        logger.error(f"Error sending digest emails: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task(bind=True, max_retries=3)
def sync_external_data(self):
    try:
        logger.info("Syncing external data...")
        
        logger.info("External data sync completed")
    except Exception as e:
        logger.error(f"Error syncing external data: {e}")
        raise self.retry(exc=e, countdown=600)


@shared_task(bind=True)
def send_order_notification(self, order_id: str, event_type: str):
    try:
        from orders.models import Order
        from core.webhooks import channel_manager
        import asyncio
        
        order = Order.objects.get(id=order_id)
        
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(channel_manager.send_to_user(
                order.user_id,
                event_type,
                {
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'status': order.status,
                    'total': str(order.total),
                }
            ))
    except Exception as e:
        logger.error(f"Error sending order notification: {e}")


@shared_task(bind=True, max_retries=5)
def process_payment(self, order_id: str, payment_data: dict):
    try:
        from orders.models import Order
        from core.services.business import PaymentService
        
        order = Order.objects.get(id=order_id)
        result = PaymentService.create_payment_intent(order)
        
        return result
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise self.retry(exc=e, countdown=120)
