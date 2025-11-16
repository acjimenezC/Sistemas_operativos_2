from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from .forms import JobForm
from services.telegram_api import publish_job_offer

def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    return render(request, 'jobs/job_list.html', {'jobs': jobs})

def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('jobs:job_list')
    else:
        form = JobForm()
    return render(request, 'jobs/job_form.html', {'form': form})

def publish_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    publish_job_offer(job)
    job.status = 'published'
    job.save()
    return redirect('jobs:job_list')
