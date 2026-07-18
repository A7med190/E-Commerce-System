import logging
from datetime import timedelta
from typing import Dict, Any, Callable
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from core.models import OutboxMessage

logger = logging.getLogger(__name__)


class OutboxService:
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.lock_timeout = timedelta(minutes=5)

    def register_handler(self, event_type: str, handler: Callable):
        self.handlers[event_type] = handler
        logger.info(f"Registered outbox handler for event type: {event_type}")

    def publish(self, event_type: str, payload: Dict[str, Any], max_retries: int = 3):
        message = OutboxMessage.objects.create(
            event_type=event_type,
            payload=payload,
            max_retries=max_retries,
        )
        logger.info(f"Published outbox message: {event_type} - {message.id}")
        return message

    def process_pending(self, batch_size: int = 100):
        now = timezone.now()
        messages = OutboxMessage.objects.filter(
            Q(processed=False),
            Q(retry_count__lt=F('max_retries')),
        ).exclude(
            lock__isnull=False,
            lock_timeout__gt=now,
        ).order_by('created_at')[:batch_size]

        for message in messages:
            self._process_message(message)

    def _process_message(self, message: OutboxMessage):
        lock_id = str(uuid.uuid4())
        lock_timeout = timezone.now() + self.lock_timeout

        updated = OutboxMessage.objects.filter(
            id=message.id,
            lock__isnull=True,
        ).update(lock=lock_id, lock_timeout=lock_timeout)

        if not updated:
            logger.debug(f"Message {message.id} is locked by another process")
            return

        try:
            message.refresh_from_db()
            handler = self.handlers.get(message.event_type)
            
            if handler:
                handler(message.payload)
            else:
                logger.warning(f"No handler registered for event type: {message.event_type}")

            message.processed = True
            message.processed_at = timezone.now()
            message.save(update_fields=['processed', 'processed_at', 'lock', 'lock_timeout'])
            logger.info(f"Successfully processed outbox message: {message.id}")

        except Exception as e:
            logger.error(f"Error processing outbox message {message.id}: {e}")
            message.retry_count += 1
            message.error_message = str(e)
            message.lock = None
            message.lock_timeout = None
            message.save(update_fields=['retry_count', 'error_message', 'lock', 'lock_timeout'])

        finally:
            if message.lock == lock_id:
                message.lock = None
                message.lock_timeout = None
                OutboxMessage.objects.filter(id=message.id).update(lock=None, lock_timeout=None)

    def cleanup_old_messages(self, days: int = 30):
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = OutboxMessage.objects.filter(
            processed=True,
            created_at__lt=cutoff,
        ).delete()
        logger.info(f"Cleaned up {deleted} old outbox messages")


outbox_service = OutboxService()
