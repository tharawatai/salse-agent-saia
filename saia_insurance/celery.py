import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saia_insurance.settings')

app = Celery('saia_insurance')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'expire-invoices-every-hour': {
        'task': 'payments.tasks.expire_old_invoices',
        'schedule': crontab(minute=0),
    },
    'send-payment-reminders': {
        'task': 'payments.tasks.send_payment_reminders',
        'schedule': crontab(hour=10, minute=0),
    },
}
