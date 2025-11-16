from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('', RedirectView.as_view(url='telegram/dashboard/', permanent=False)),
    path('telegram/', include('apps.telegram_agent.urls')),
    path('jobs/', include('apps.jobs.urls')),
    path('analytics/', include('apps.analytics.urls')),
]
