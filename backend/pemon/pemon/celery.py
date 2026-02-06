import os

from celery import Celery
from celery.schedules import crontab
from decouple import config

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    config('DJANGO_SETTINGS_MODULE', default='pemon.settings.development')
)

app = Celery('pemon')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Debug task to test Celery configuration.
    
    This task prints the request details for debugging purposes.
    Use this to verify that Celery is working correctly.
    
    Usage:
        from pemon.celery import debug_task
        debug_task.delay()
    """
    print(f'Request: {self.request!r}')


# CELERY BEAT SCHEDULE (Periodic Tasks)

app.conf.beat_schedule = {
    # Example: Run daily reconciliation at 1 AM
    'daily-reconciliation': {
        'task': 'transactions.tasks.run_daily_reconciliation',
        'schedule': crontab(hour=1, minute=0),
    },
    
    # Example: Process pending settlements at 2 AM
    'process-settlements': {
        'task': 'wallets.tasks.process_pending_settlements',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Example: Send daily summary emails at 6 AM
    'send-daily-summaries': {
        'task': 'core.tasks.send_daily_summary_emails',
        'schedule': crontab(hour=6, minute=0),
    },
    
    # Example: Clean up expired sessions every hour
    'cleanup-expired-sessions': {
        'task': 'core.tasks.cleanup_expired_sessions',
        'schedule': crontab(minute=0),  # Every hour
    },
    
    # Example: Update currency exchange rates every 4 hours
    'update-exchange-rates': {
        'task': 'core.tasks.update_exchange_rates',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },
    
    # Example: Check and process KYC expirations daily at midnight
    'check-kyc-expirations': {
        'task': 'kyc.tasks.check_kyc_expirations',
        'schedule': crontab(hour=0, minute=0),
    },
}


# CELERY TASK CONFIGURATION

app.conf.update(
    # Task result backend
    result_backend='django-db',
    result_extended=True,
    
    # Task routing (different queues for different priorities)
    task_routes={
        'core.tasks.send_email': {'queue': 'emails'},
        'core.tasks.send_sms': {'queue': 'sms'},
        'transactions.tasks.*': {'queue': 'transactions'},
        'kyc.tasks.*': {'queue': 'kyc'},
    },
    
    # Task priority
    task_queue_max_priority=10,
    task_default_priority=5,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result expiration
    result_expires=3600,  # 1 hour
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='Africa/Lagos',
    enable_utc=True,
)


# CELERY SIGNALS

from celery.signals import task_failure, task_success


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """
    Handle task failures.
    
    This signal is triggered when a task fails. Use it to log errors,
    send notifications, or perform cleanup operations.
    """
    import logging
    logger = logging.getLogger('celery')
    logger.error(
        f'Task {sender.name}[{task_id}] failed: {exception}',
        exc_info=True,
        extra={'task_id': task_id, 'task_name': sender.name}
    )


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """
    Handle task success.
    
    This signal is triggered when a task completes successfully.
    Use it for logging or triggering dependent tasks.
    """
    import logging
    logger = logging.getLogger('celery')
    logger.info(f'Task {sender.name} completed successfully')