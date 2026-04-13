import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from django.db import transaction, models
from django.core.cache import cache
from products.models import Product, Inventory
from orders.models import Order, OrderItem
from users.models import User

logger = logging.getLogger(__name__)


class InventoryService:
    CACHE_PREFIX = 'inventory:'
    CACHE_TTL = 300

    @classmethod
    def get_stock(cls, product_id: str) -> int:
        cache_key = f"{cls.CACHE_PREFIX}{product_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            inventory = Inventory.objects.select_related('product').get(product_id=product_id)
            cache.set(cache_key, inventory.stock_quantity, timeout=cls.CACHE_TTL)
            return inventory.stock_quantity
        except Inventory.DoesNotExist:
            return 0

    @classmethod
    def reserve_stock(cls, product_id: str, quantity: int) -> bool:
        cache_key = f"{cls.CACHE_PREFIX}{product_id}"
        
        with transaction.atomic():
            inventory = Inventory.objects.select_for_update().get(product_id=product_id)
            
            if inventory.stock_quantity < quantity:
                logger.warning(f"Insufficient stock for product {product_id}: requested {quantity}, available {inventory.stock_quantity}")
                return False
            
            inventory.stock_quantity -= quantity
            inventory.save(update_fields=['stock_quantity'])
            
            cache.set(cache_key, inventory.stock_quantity, timeout=cls.CACHE_TTL)
            logger.info(f"Reserved {quantity} units of product {product_id}")
            return True

    @classmethod
    def release_stock(cls, product_id: str, quantity: int):
        cache_key = f"{cls.CACHE_PREFIX}{product_id}"
        
        with transaction.atomic():
            inventory = Inventory.objects.select_for_update().get(product_id=product_id)
            inventory.stock_quantity += quantity
            inventory.save(update_fields=['stock_quantity'])
            
            cache.set(cache_key, inventory.stock_quantity, timeout=cls.CACHE_TTL)
            logger.info(f"Released {quantity} units of product {product_id}")

    @classmethod
    def check_low_stock(cls, product_id: str) -> bool:
        try:
            inventory = Inventory.objects.get(product_id=product_id)
            return inventory.is_low_stock
        except Inventory.DoesNotExist:
            return False

    @classmethod
    def get_low_stock_products(cls) -> List[Dict[str, Any]]:
        return list(Inventory.objects.filter(
            stock_quantity__lte=models.F('low_stock_threshold')
        ).select_related('product').values(
            'product__id', 'product__name', 'stock_quantity', 'low_stock_threshold'
        ))


class OrderService:
    @classmethod
    @transaction.atomic
    def create_order(cls, user: User, items: List[Dict], shipping_address: Dict) -> Order:
        order = Order.objects.create(
            user=user,
            shipping_address=shipping_address,
            status='pending',
        )

        subtotal = Decimal('0')
        
        for item in items:
            product = Product.objects.get(id=item['product_id'])
            
            if not InventoryService.reserve_stock(product.id, item['quantity']):
                raise ValueError(f"Insufficient stock for {product.name}")
            
            item_total = product.base_price * item['quantity']
            
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_price=product.base_price,
                quantity=item['quantity'],
                customizations=item.get('customizations', []),
                total=item_total,
            )
            
            subtotal += item_total

        order.subtotal = subtotal
        order.tax = subtotal * Decimal('0.08')
        order.total = order.subtotal + order.tax + order.shipping_cost
        order.save()

        logger.info(f"Created order {order.order_number} for user {user.id}")
        return order

    @classmethod
    def cancel_order(cls, order_id: str, reason: str = None) -> Order:
        order = Order.objects.select_for_update().get(id=order_id)
        
        if order.status in ['delivered', 'cancelled', 'refunded']:
            raise ValueError(f"Cannot cancel order in status: {order.status}")
        
        for item in order.items.all():
            InventoryService.release_stock(item.product_id, item.quantity)
        
        order.status = 'cancelled'
        order.notes = f"{order.notes}\nCancelled: {reason}" if reason else order.notes
        order.save()
        
        logger.info(f"Cancelled order {order.order_number}")
        return order


class NotificationService:
    @classmethod
    def send_order_confirmation(cls, order: Order):
        logger.info(f"Sending order confirmation for {order.order_number}")
        from core.webhooks import channel_manager
        import asyncio
        
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(channel_manager.send_to_user(
                order.user_id,
                'order_update',
                {
                    'order_id': str(order.id),
                    'order_number': order.order_number,
                    'status': order.status,
                    'total': str(order.total),
                }
            ))

    @classmethod
    def send_low_stock_alert(cls, product: Product, current_stock: int):
        logger.info(f"Low stock alert for {product.name}: {current_stock}")


class PaymentService:
    @classmethod
    def create_payment_intent(cls, order: Order) -> Dict:
        import stripe
        from django.conf import settings
        
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe not configured")
        
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),
            currency='usd',
            metadata={
                'order_id': str(order.id),
                'order_number': order.order_number,
            }
        )
        
        return {
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
        }

    @classmethod
    def process_webhook(cls, payload: bytes, signature: str) -> Dict:
        import stripe
        from django.conf import settings
        
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ValueError("Stripe webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")
