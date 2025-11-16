from django.db import models
from django.contrib.auth.models import User

class TelegramUser(models.Model):
    """Modelo para usuarios de Telegram"""
    telegram_id = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='es')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Telegram User'
        verbose_name_plural = 'Telegram Users'

    def __str__(self):
        return f"{self.username or self.telegram_id} ({self.first_name})"


class TelegramMessage(models.Model):
    """Modelo para mensajes de Telegram"""
    MESSAGE_TYPE = (
        ('text', 'Texto'),
        ('command', 'Comando'),
        ('photo', 'Foto'),
        ('document', 'Documento'),
        ('voice', 'Voz'),
    )
    
    DIRECTION = (
        ('incoming', 'Entrante'),
        ('outgoing', 'Saliente'),
    )

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE, default='text')
    direction = models.CharField(max_length=20, choices=DIRECTION, default='incoming')
    telegram_message_id = models.IntegerField(null=True, blank=True)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Telegram Message'
        verbose_name_plural = 'Telegram Messages'

    def __str__(self):
        return f"{self.user} - {self.direction} - {self.content[:50]}"


class AIResponse(models.Model):
    """Modelo para respuestas de IA generadas por Gemini"""
    STATUS = (
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('failed', 'Fallida'),
        ('rated', 'Evaluada'),
    )

    message = models.OneToOneField(TelegramMessage, on_delete=models.CASCADE, related_name='ai_response')
    response_text = models.TextField()
    confidence_score = models.FloatField(default=0.0)
    model_used = models.CharField(max_length=50, default='gemini-pro')
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    feedback = models.TextField(blank=True, null=True)
    feedback_score = models.IntegerField(null=True, blank=True, help_text="1-5 rating from admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Response'
        verbose_name_plural = 'AI Responses'

    def __str__(self):
        return f"AI Response to {self.message.user} - {self.status}"


class Broadcast(models.Model):
    """Modelo para broadcasts programados"""
    STATUS = (
        ('draft', 'Borrador'),
        ('scheduled', 'Programado'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
    )

    title = models.CharField(max_length=255)
    content = models.TextField()
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Broadcast'
        verbose_name_plural = 'Broadcasts'

    def __str__(self):
        return f"{self.title} - {self.status}"


class TelegramConfig(models.Model):
    """Modelo para configuración del bot de Telegram"""
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Telegram Config'
        verbose_name_plural = 'Telegram Configs'

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


# ============ MODELOS PARA ENCUESTAS ============

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