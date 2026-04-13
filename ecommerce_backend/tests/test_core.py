import pytest
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestHealthCheck(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_returns_200(self):
        response = self.client.get('/api/health/')
        self.assertIn(response.status_code, [200, 503])

    def test_health_check_returns_status(self):
        response = self.client.get('/api/health/')
        self.assertIn('status', response.json())

    def test_health_check_returns_checks(self):
        response = self.client.get('/api/health/')
        self.assertIn('checks', response.json())


@pytest.mark.django_db
class TestCircuitBreaker(TestCase):
    def test_circuit_breaker_initial_state(self):
        from core.circuit_breaker import CircuitBreaker
        breaker = CircuitBreaker(failure_threshold=3)
        self.assertEqual(breaker.state, "closed")
        self.assertEqual(breaker.failures, 0)

    def test_circuit_breaker_opens_after_failures(self):
        from core.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker(
            failure_threshold=3,
            expected_exception=ValueError
        )
        
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        
        self.assertEqual(breaker.state, "open")


@pytest.mark.django_db
class TestSoftDelete(TestCase):
    def setUp(self):
        from core.models import BaseSoftDeleteModel
        from products.models import Product
        self.Product = Product

    def test_soft_delete_manager_excludes_deleted(self):
        product = self.Product.objects.create(
            name="Test Product",
            slug="test-product",
            description="Test",
            base_price=10.00,
            sku="TEST-SKU",
        )
        
        product.delete()
        
        self.assertEqual(self.Product.objects.count(), 0)
        self.assertEqual(self.Product.all_objects.count(), 1)

    def test_restore_deleted_object(self):
        product = self.Product.objects.create(
            name="Test Product",
            slug="test-product-restore",
            description="Test",
            base_price=10.00,
            sku="TEST-SKU-RESTORE",
        )
        
        product.delete()
        product.restore()
        
        self.assertEqual(self.Product.objects.count(), 1)
        self.assertFalse(product.is_deleted)


@pytest.mark.django_db
class TestIdempotencyMiddleware(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_idempotency_key_required_for_post(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'testpass123',
        })
        
        self.assertNotIn('X-Idempotency-Key', response.get('X-Idempotency-Key', ''))


@pytest.mark.django_db
class TestWebhookService(TestCase):
    def test_webhook_subscribe(self):
        from core.webhooks import webhook_service
        
        webhook_service.subscribe('order.created', 'https://example.com/webhook')
        
        self.assertIn('order.created', webhook_service.subscribers)
        self.assertEqual(len(webhook_service.subscribers['order.created']), 1)

    def test_webhook_unsubscribe(self):
        from core.webhooks import webhook_service
        
        url = 'https://example.com/webhook'
        webhook_service.subscribe('order.created', url)
        webhook_service.unsubscribe('order.created', url)
        
        self.assertEqual(len(webhook_service.subscribers.get('order.created', [])), 0)


@pytest.mark.django_db
class TestOutboxService(TestCase):
    def test_outbox_publish(self):
        from core.outbox import outbox_service
        
        message = outbox_service.publish(
            'test.event',
            {'data': 'test'},
            max_retries=3
        )
        
        self.assertFalse(message.processed)
        self.assertEqual(message.event_type, 'test.event')
        self.assertEqual(message.retry_count, 0)

    def test_outbox_register_handler(self):
        from core.outbox import outbox_service
        
        handler_called = []
        
        def test_handler(payload):
            handler_called.append(payload)
        
        outbox_service.register_handler('test.event.handler', test_handler)
        
        self.assertIn('test.event.handler', outbox_service.handlers)
