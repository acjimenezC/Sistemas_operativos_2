from django.urls import path
from . import views

app_name = 'telegram_agent'
urlpatterns = [
    # Webhook
    path('webhook/', views.webhook, name='webhook'),
    
    # Dashboard y panel
    path('dashboard/', views.dashboard, name='dashboard'),
    path('conversations/', views.conversations, name='conversations'),
    path('analytics/', views.analytics, name='analytics'),
    path('image-generator/', views.image_generator, name='image_generator'),
    
    # APIs
    path('api/generate-image/', views.generate_image, name='generate_image'),
    path('api/publish-image/', views.publish_image, name='publish_image'),
    path('api/feedback/<int:response_id>/', views.feedback_response, name='feedback_response'),
    
    # Encuestas
    path('surveys/', views.surveys_list, name='surveys_list'),
    path('surveys/<int:survey_id>/', views.survey_detail, name='survey_detail'),
    path('surveys/<int:survey_id>/results/', views.survey_results, name='survey_results'),
    path('surveys/create-with-ai/', views.create_survey_with_ai, name='create_survey_with_ai'),
]
