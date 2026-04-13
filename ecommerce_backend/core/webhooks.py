import uuid
import json
import logging
from datetime import timedelta
from typing import Dict, Any, Callable, Optional
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class WebhookDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    webhook_url = models.URLField(max_length=500)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)
    next_retry = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['success', 'next_retry']),
            models.Index(fields=['webhook_url', 'event_type']),
        ]

    def __str__(self):
        return f"{self.event_type} -> {self.webhook_url} ({self.attempts}/{self.max_attempts})"


class WebhookService:
    def __init__(self):
        self.subscribers: Dict[str, list] = {}

    def subscribe(self, event_type: str, url: str, secret: str = None, headers: Dict = None):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        subscriber = {
            'url': url,
            'secret': secret,
            'headers': headers or {},
        }
        
        if subscriber not in self.subscribers[event_type]:
            self.subscribers[event_type].append(subscriber)
            logger.info(f"Subscribed {url} to event type: {event_type}")

    def unsubscribe(self, event_type: str, url: str):
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                s for s in self.subscribers[event_type] if s['url'] != url
            ]

    def publish(self, event_type: str, payload: Dict[str, Any]):
        if event_type not in self.subscribers:
            logger.debug(f"No subscribers for event type: {event_type}")
            return []

        deliveries = []
        for subscriber in self.subscribers[event_type]:
            delivery = self._create_delivery(event_type, subscriber, payload)
            deliveries.append(delivery)
        
        return deliveries

    def _create_delivery(self, event_type: str, subscriber: Dict, payload: Dict) -> WebhookDelivery:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'ECommerce-Webhook/1.0',
            'X-Webhook-Event': event_type,
            **subscriber.get('headers', {}),
        }

        delivery = WebhookDelivery.objects.create(
            webhook_url=subscriber['url'],
            event_type=event_type,
            payload=payload,
            headers=headers,
        )

        if subscriber.get('secret'):
            import hmac
            import hashlib
            payload_bytes = json.dumps(payload).encode()
            signature = hmac.new(
                subscriber['secret'].encode(),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f"sha256={signature}"

        self._attempt_delivery(delivery)
        return delivery

    def _attempt_delivery(self, delivery: WebhookDelivery):
        import httpx

        delivery.attempts += 1
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    delivery.webhook_url,
                    json=delivery.payload,
                    headers=delivery.headers,
                )
            
            delivery.status_code = response.status_code
            delivery.response_body = response.text[:1000]
            delivery.success = 200 <= response.status_code < 300
            
            if delivery.success:
                delivery.completed_at = timezone.now()
                logger.info(f"Webhook delivered successfully: {delivery.id}")
            else:
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                self._schedule_retry(delivery)

        except Exception as e:
            delivery.error_message = str(e)
            self._schedule_retry(delivery)

        delivery.save()

    def _schedule_retry(self, delivery: WebhookDelivery):
        if delivery.attempts < delivery.max_attempts:
            delays = [60, 300, 900, 3600, 7200]
            delay = delays[min(delivery.attempts - 1, len(delays) - 1)]
            delivery.next_retry = timezone.now() + timedelta(seconds=delay)
            logger.info(f"Scheduled retry for delivery {delivery.id} in {delay}s")

    def process_pending_retries(self, batch_size: int = 100):
        pending = WebhookDelivery.objects.filter(
            success=False,
            attempts__lt=models.F('max_attempts'),
            next_retry__lte=timezone.now(),
        )[:batch_size]

        for delivery in pending:
            delivery.next_retry = None
            delivery.save()
            self._attempt_delivery(delivery)

    def cleanup_old_deliveries(self, days: int = 30):
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = WebhookDelivery.objects.filter(
            success=True,
            completed_at__lt=cutoff,
        ).delete()
        logger.info(f"Cleaned up {deleted} old webhook deliveries")


webhook_service = WebhookService()
