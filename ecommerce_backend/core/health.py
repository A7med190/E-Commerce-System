import logging
import time
from typing import Dict, Any
from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger(__name__)


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    checks = serializers.DictField()


class DatabaseHealthCheck:
    name = "database"

    def check(self) -> Dict[str, Any]:
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def get_latency(self) -> float:
        start = time.time()
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return (time.time() - start) * 1000


class CacheHealthCheck:
    name = "cache"

    def check(self) -> Dict[str, Any]:
        try:
            from django.core.cache import cache
            test_key = "health_check_test"
            cache.set(test_key, "ok", 10)
            value = cache.get(test_key)
            cache.delete(test_key)
            
            if value == "ok":
                return {"status": "healthy"}
            return {"status": "unhealthy", "error": "Cache read/write failed"}
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


class CeleryHealthCheck:
    name = "celery"

    def check(self) -> Dict[str, Any]:
        try:
            from ecommerce_backend.celery import app
            inspect = app.control.inspect()
            
            active_workers = inspect.active()
            
            if active_workers:
                return {"status": "healthy", "workers": list(active_workers.keys())}
            return {"status": "degraded", "workers": []}
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


class DiskSpaceHealthCheck:
    name = "disk"

    def check(self) -> Dict[str, Any]:
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            percent_used = (used / total) * 100
            
            return {
                "status": "healthy" if percent_used < 90 else "degraded",
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "percent_used": round(percent_used, 1),
            }
        except Exception as e:
            logger.error(f"Disk space health check failed: {e}")
            return {"status": "unknown", "error": str(e)}


class ExternalServicesHealthCheck:
    name = "external_services"

    def check(self) -> Dict[str, Any]:
        results = {}
        
        if hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
            results['stripe'] = self._check_stripe()
        
        if hasattr(settings, 'REDIS_URL'):
            results['redis'] = self._check_redis()
        
        return {
            "status": "healthy" if all(r.get("status") == "healthy" for r in results.values()) else "degraded",
            "services": results,
        }

    def _check_stripe(self) -> Dict[str, Any]:
        try:
            import stripe
            if not settings.STRIPE_SECRET_KEY:
                return {"status": "skipped", "reason": "Not configured"}
            
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.Account.retrieve("me")
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_redis(self) -> Dict[str, Any]:
        try:
            import redis
            from urllib.parse import urlparse
            
            url = getattr(settings, 'REDIS_URL', 'redis://127.0.0.1:6379')
            parsed = urlparse(url)
            
            r = redis.Redis(host=parsed.hostname, port=parsed.port or 6379, db=0)
            r.ping()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


class HealthCheckRegistry:
    _instance = None
    _checks = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._register_default_checks()
        return cls._instance

    def _register_default_checks(self):
        self._checks = [
            DatabaseHealthCheck(),
            CacheHealthCheck(),
            CeleryHealthCheck(),
            DiskSpaceHealthCheck(),
            ExternalServicesHealthCheck(),
        ]

    def register(self, check):
        self._checks.append(check)

    def run_all(self) -> Dict[str, Any]:
        from django.utils import timezone
        
        results = {}
        overall_status = "healthy"
        
        for check in self._checks:
            try:
                result = check.check()
                results[check.name] = result
                
                if result.get("status") == "unhealthy":
                    overall_status = "unhealthy"
                elif result.get("status") == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
            except Exception as e:
                logger.error(f"Health check {check.name} raised exception: {e}")
                results[check.name] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": timezone.now(),
            "checks": results,
        }


health_check_registry = HealthCheckRegistry()
