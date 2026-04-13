import logging
from celery import Celery
from celery.schedules import crontab

os = __import__('os')

app = Celery("ecommerce_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process-outbox-messages': {
        'task': 'core.tasks.process_outbox_messages',
        'schedule': 10.0,
    },
    'process-webhook-retries': {
        'task': 'core.tasks.process_webhook_retries',
        'schedule': 60.0,
    },
    'cleanup-old-data': {
        'task': 'core.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),
    },
    'check-low-stock': {
        'task': 'core.tasks.check_low_stock',
        'schedule': crontab(minute='*/15'),
    },
    'send-digest-emails': {
        'task': 'core.tasks.send_digest_emails',
        'schedule': crontab(hour=8, minute=0),
    },
    'sync-external-data': {
        'task': 'core.tasks.sync_external_data',
        'schedule': crontab(minute='*/30'),
    },
}

app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
app.conf.beat_scheduler_class = 'django_celery_beat.schedulers:DatabaseScheduler'

app.conf.task_routes = {
    'core.tasks.*': {'queue': 'default'},
    'orders.tasks.*': {'queue': 'orders'},
    'products.tasks.*': {'queue': 'products'},
}

app.conf.task_annotations = {
    'core.tasks.process_outbox_messages': {'rate_limit': '10/m'},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
