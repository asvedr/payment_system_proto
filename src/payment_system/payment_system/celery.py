import os

from celery import Celery

from serje import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serje.settings')
app = Celery('serje', broker=settings.CELERY_BROKER_URL)
app.autodiscover_tasks()
