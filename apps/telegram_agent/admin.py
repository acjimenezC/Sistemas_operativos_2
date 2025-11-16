from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TelegramUser, TelegramMessage, AIResponse, Broadcast, TelegramConfig,
    Survey, SurveyQuestion, SurveyOption, SurveyResponse, SurveyAnswer
)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'is_active', 'is_admin', 'created_at')
    list_filter = ('is_active', 'is_admin', 'created_at')
    search_fields = ('telegram_id', 'username', 'first_name', 'email')
    readonly_fields = ('telegram_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Personal', {
            'fields': ('telegram_id', 'username', 'first_name', 'last_name', 'phone', 'email')
        }),
        ('Configuración', {
            'fields': ('is_active', 'is_admin', 'language')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(TelegramMessage)
class TelegramMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_type', 'direction', 'content_preview', 'created_at')
    list_filter = ('message_type', 'direction', 'created_at')
    search_fields = ('user__username', 'content')
    readonly_fields = ('user', 'telegram_message_id', 'created_at', 'content_display')
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Contenido'
    
    def content_display(self, obj):
        return format_html('<pre>{}</pre>', obj.content)
    content_display.short_description = 'Contenido Completo'


@admin.register(AIResponse)
class AIResponseAdmin(admin.ModelAdmin):
    list_display = ('message_user', 'status_badge', 'model_used', 'feedback_score', 'created_at')
    list_filter = ('status', 'model_used', 'created_at')
    search_fields = ('message__user__username', 'response_text')
    readonly_fields = ('message', 'created_at', 'updated_at', 'response_display')
    fieldsets = (
        ('Mensaje Asociado', {
            'fields': ('message',)
        }),
        ('Respuesta', {
            'fields': ('response_display', 'model_used', 'confidence_score')
        }),
        ('Estado y Feedback', {
            'fields': ('status', 'feedback', 'feedback_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_user(self, obj):
        return obj.message.user.username
    message_user.short_description = 'Usuario'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'sent': '#00AA00',
            'failed': '#FF0000',
            'rated': '#0000FF',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#808080'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def response_display(self, obj):
        return format_html('<pre>{}</pre>', obj.response_text)
    response_display.short_description = 'Respuesta Completa'


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('title', 'status_badge', 'scheduled_at', 'sent_count', 'failed_count', 'created_by')
    list_filter = ('status', 'scheduled_at', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('sent_count', 'failed_count', 'created_at', 'updated_at', 'content_display')
    fieldsets = (
        ('Información', {
            'fields': ('title', 'content_display', 'created_by')
        }),
        ('Programación', {
            'fields': ('scheduled_at', 'status')
        }),
        ('Estadísticas', {
            'fields': ('sent_count', 'failed_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': '#808080',
            'scheduled': '#FFA500',
            'sending': '#FFD700',
            'sent': '#00AA00',
            'failed': '#FF0000',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#808080'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def content_display(self, obj):
        return format_html('<pre>{}</pre>', obj.content)
    content_display.short_description = 'Contenido'


@admin.register(TelegramConfig)
class TelegramConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('updated_at',)
    
    def value_preview(self, obj):
        return obj.value[:100] + '...' if len(obj.value) > 100 else obj.value
    value_preview.short_description = 'Valor'


# ============ ADMIN PARA ENCUESTAS ============

class SurveyOptionInline(admin.TabularInline):
    model = SurveyOption
    extra = 2
    fields = ['option_text', 'order']


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1
    fields = ['question_text', 'question_type', 'is_required', 'order']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'survey_type', 'status_badge', 'response_count', 'created_at']
    list_filter = ['status', 'survey_type', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('title', 'description', 'survey_type', 'status')
        }),
        ('Configuración', {
            'fields': ('created_by', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SurveyQuestionInline]
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def status_badge(self, obj):
        colors = {
            'active': '#7EFFA2',
            'closed': '#999',
            'draft': '#FF9800'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#999'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def response_count(self, obj):
        completed = obj.responses.filter(is_completed=True).count()
        total = obj.responses.count()
        return f"{completed}/{total}"
    response_count.short_description = 'Respuestas'


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ['survey', 'question_text', 'question_type', 'is_required', 'order']
    list_filter = ['question_type', 'is_required', 'survey']
    search_fields = ['question_text', 'survey__title']
    inlines = [SurveyOptionInline]
    fieldsets = (
        ('Información', {
            'fields': ('survey', 'question_text', 'question_type', 'is_required', 'order')
        }),
    )


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'user', 'completion_badge', 'started_at', 'completed_at']
    list_filter = ['is_completed', 'survey', 'started_at']
    search_fields = ['user__username', 'survey__title']
    readonly_fields = ['started_at', 'completed_at', 'survey', 'user']
    
    def completion_badge(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green; font-weight: bold;">✅ Completada</span>')
        return format_html('<span style="color: orange; font-weight: bold;">⏳ En progreso</span>')
    completion_badge.short_description = 'Estado'
    
    def has_add_permission(self, request):
        return False  # Solo lectura


@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ['response', 'question', 'answer_preview', 'answered_at']
    list_filter = ['answered_at']
    search_fields = ['response__user__username']
    readonly_fields = ['answered_at']
    
    def answer_preview(self, obj):
        if obj.selected_option:
            return obj.selected_option.option_text
        elif obj.rating:
            return f"⭐ {obj.rating}/5"
        else:
            return obj.answer_text[:50] + '...' if obj.answer_text else '-'
    answer_preview.short_description = 'Respuesta'
    
    def has_add_permission(self, request):
        return False  # Solo lectura
