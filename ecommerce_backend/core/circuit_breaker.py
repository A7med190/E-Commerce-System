import uuid
import hashlib
import time
import logging
from functools import wraps
from typing import Optional, Any, Callable
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"

    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half-open"
                logger.info("Circuit breaker entering half-open state")
            else:
                raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.reset()
            return result
        except self.expected_exception as e:
            self.record_failure()
            raise

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
            logger.warning("Circuit breaker opened")

    def reset(self):
        self.failures = 0
        self.state = "closed"
        self.last_failure_time = None


class CircuitBreakerOpen(Exception):
    pass


circuit_breakers = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(**kwargs)
    return circuit_breakers[name]


def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    def decorator(func: Callable) -> Callable:
        breaker_name = f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            breaker = get_circuit_breaker(
                breaker_name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def idempotency_key_generator(request) -> str:
    if settings.DEBUG:
        return f"idempotency:{request.META.get('HTTP_X_IDEMPOTENCY_KEY', str(uuid.uuid4()))}"
    return f"idempotency:{request.META['HTTP_X_IDEMPOTENCY_KEY']}"


class IdempotencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in ('POST', 'PATCH', 'PUT'):
            return self.get_response(request)

        idempotency_key = request.META.get('HTTP_X_IDEMPOTENCY_KEY')
        if not idempotency_key:
            return self.get_response(request)

        cache_key = f"idempotency:{idempotency_key}"
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
            return JsonResponse(cached_response['data'], status=cached_response['status'])

        response = self.get_response(request)

        if response.status_code < 400:
            try:
                response_data = {
                    'data': response.data if hasattr(response, 'data') else {},
                    'status': response.status_code,
                }
                cache.set(cache_key, response_data, timeout=86400)
            except Exception:
                pass

        return response


def idempotent(key_prefix: str = "", ttl: int = 86400):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [key_prefix, func.__name__]
            for arg in args:
                if isinstance(arg, (str, int, uuid.UUID)):
                    key_parts.append(str(arg))
            cache_key = ":".join(key_parts)
            
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=ttl)
            return result
        return wrapper
    return decorator
