# Minimal scheduler example (not auto-started)
from apscheduler.schedulers.background import BackgroundScheduler
from apps.jobs.models import Job
from services.telegram_api import publish_job_offer

def start_scheduler():
    scheduler = BackgroundScheduler()
    def task():
        jobs = Job.objects.filter(status='draft')
        for job in jobs:
            publish_job_offer(job)
            job.status = 'published'
            job.save()
    scheduler.add_job(task, 'interval', hours=24)
    scheduler.start()
    return scheduler
