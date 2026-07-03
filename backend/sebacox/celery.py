import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sebacox.settings')

app = Celery('sebacox')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'core.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'send-pending-notifications': {
        'task': 'core.tasks.send_pending_notifications',
        'schedule': crontab(minute=0),  # Every hour
    },
}
