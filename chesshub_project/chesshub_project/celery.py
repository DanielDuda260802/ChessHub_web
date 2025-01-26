import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chesshub_project.settings')
app = Celery("chesshub_project")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.beat_schedule = {
    'refresh_fen_cache_every_hour': {
        'task': 'main.tasks.refresh_fen_cache',
        'schedule': crontab(minute=5),  
    },
}

app.autodiscover_tasks()