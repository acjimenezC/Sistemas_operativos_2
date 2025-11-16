"""
Modelos para el sistema de encuestas
"""
from django.db import models
from django.contrib.auth.models import User
from .models import TelegramUser


class Survey(models.Model):
    """Modelo para encuestas"""
    SURVEY_TYPES = [
        ('salary', 'Salarios'),
        ('events', 'Eventos'),
        ('wellness', 'Bienestar'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('closed', 'Cerrada'),
        ('draft', 'Borrador'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class SurveyQuestion(models.Model):
    """Preguntas de la encuesta"""
    QUESTION_TYPES = [
        ('multiple', 'Opción múltiple'),
        ('text', 'Texto libre'),
        ('rating', 'Calificación (1-5)'),
        ('yes_no', 'Sí/No'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.question_text[:50]


class SurveyOption(models.Model):
    """Opciones para preguntas de opción múltiple"""
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.option_text


class SurveyResponse(models.Model):
    """Respuestas de usuarios a encuestas"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['survey', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.survey.title}"


class SurveyAnswer(models.Model):
    """Respuestas individuales a preguntas"""
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    
    answer_text = models.TextField(blank=True, null=True)
    selected_option = models.ForeignKey(SurveyOption, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)  # Para calificaciones 1-5
    
    answered_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Respuesta a {self.question.question_text[:30]}"
