import os

from celery import Celery

from payment_system import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_system.settings')
app = Celery('payment_system', broker=settings.CELERY_BROKER_URL)
app.autodiscover_tasks()
