# project/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('project')

app.conf.beat_schedule = {
    'check-water-levels-every-hour': {
        'task': 'sms.tasks.check_and_send_alerts',
        'schedule': crontab(minute=0, hour='*'),  # Every hour
    },
}
