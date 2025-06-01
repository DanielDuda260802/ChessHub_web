import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_ready

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chesshub_project.settings')

app = Celery("chesshub_project")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    task_ignore_result=True,
)

app.conf.beat_schedule = {
    'refresh_fen_cache_every_six_hours': {
        'task': 'main.tasks.refresh_fen_cache',
        'schedule': 10,  
    },
}
app.conf.timezone = 'UTC'

app.autodiscover_tasks()