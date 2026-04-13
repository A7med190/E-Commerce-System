import time
import logging
import uuid
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
        request.request_id = str(uuid.uuid4())
        
        logger.info(
            f"[{request.request_id}] {request.method} {request.path}",
            extra={
                'request_id': request.request_id,
                'method': request.method,
                'path': request.path,
                'user': getattr(request, 'user', None),
            }
        )

    def process_response(self, request, response):
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        logger.info(
            f"[{getattr(request, 'request_id', 'unknown')}] "
            f"{request.method} {request.path} - {response.status_code} ({duration:.3f}s)",
            extra={
                'request_id': getattr(request, 'request_id', 'unknown'),
                'status_code': response.status_code,
                'duration': duration,
            }
        )
        
        response['X-Request-ID'] = getattr(request, 'request_id', '')
        response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

    def process_exception(self, request, exception):
        logger.error(
            f"[{getattr(request, 'request_id', 'unknown')}] Exception: {exception}",
            exc_info=True,
            extra={
                'request_id': getattr(request, 'request_id', 'unknown'),
                'path': request.path,
                'method': request.method,
            }
        )


class IdempotencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in ('POST', 'PATCH', 'PUT'):
            return self.get_response(request)

        from django.conf import settings
        from django.core.cache import cache
        
        idempotency_key = request.META.get('HTTP_X_IDEMPOTENCY_KEY')
        if not idempotency_key:
            return self.get_response(request)

        cache_key = f"idempotency:{idempotency_key}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
            return JsonResponse(
                cached_response['data'],
                status=cached_response['status']
            )

        response = self.get_response(request)

        if response.status_code < 400:
            try:
                response_data = {
                    'data': response.data if hasattr(response, 'data') else {},
                    'status': response.status_code,
                }
                cache.set(
                    cache_key,
                    response_data,
                    timeout=getattr(settings, 'IDEMPOTENCY_CACHE_TTL', 86400)
                )
            except Exception:
                pass

        return response


class CircuitBreakerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings
        from core.circuit_breaker import CircuitBreakerOpen
        
        breaker_name = f"http_{request.method}_{request.path}"
        
        try:
            response = self.get_response(request)
            return response
        except CircuitBreakerOpen:
            return JsonResponse(
                {
                    'error': 'Service temporarily unavailable',
                    'code': 'CIRCUIT_OPEN',
                },
                status=503
            )


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.core.cache import cache
        from django.conf import settings
        
        client_ip = self._get_client_ip(request)
        cache_key = f"rate_limit:{client_ip}"
        
        limit = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
        timeout = 60
        
        current = cache.get(cache_key, 0)
        
        if current >= limit:
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'retry_after': timeout,
                },
                status=429
            )
        
        cache.set(cache_key, current + 1, timeout)
        
        response = self.get_response(request)
        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(max(0, limit - current - 1))
        
        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
