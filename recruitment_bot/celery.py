"""
Configuración de Celery para tareas asincrónicas
"""
import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment_bot.settings')

app = Celery('recruitment_bot')

# Usar configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubrir tareas automáticamente
app.autodiscover_tasks()

# Configuración de Celery Beat (programador)
app.conf.beat_schedule = {
    'send-pending-broadcasts': {
        'task': 'apps.telegram_agent.tasks.send_scheduled_broadcasts',
        'schedule': crontab(minute='*/5'),  # Cada 5 minutos
    },
    'analyze-ai-feedback': {
        'task': 'apps.telegram_agent.tasks.analyze_feedback',
        'schedule': crontab(hour='*/1'),  # Cada hora
    },
    'cleanup-old-messages': {
        'task': 'apps.telegram_agent.tasks.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0),  # Cada día a las 3 AM
    },
}

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@app.task(bind=True)
def debug_task(self):
    """Tarea de debug"""
    print(f'Request: {self.request!r}')
