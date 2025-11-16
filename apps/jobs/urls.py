from django.urls import path
from . import views

app_name = 'jobs'
urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('create/', views.job_create, name='job_create'),
    path('publish/<int:job_id>/', views.publish_job, name='publish_job'),
]
