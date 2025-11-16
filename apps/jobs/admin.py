from django.contrib import admin
from django.utils.html import format_html
from .models import Job, JobOffer


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'remote_type', 'status_badge', 'views_count', 'salary_range', 'published_at')
    list_filter = ('status', 'remote', 'created_at', 'published_at')
    search_fields = ('title', 'company', 'description', 'requirements')
    readonly_fields = ('views_count', 'applications_count', 'created_at', 'updated_at', 'published_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'company')
        }),
        ('Descripción y Requisitos', {
            'fields': ('description', 'requirements', 'benefits')
        }),
        ('Detalles de Ubicación y Tipo', {
            'fields': ('location', 'remote')
        }),
        ('Compensación', {
            'fields': ('salary_min', 'salary_max', 'currency')
        }),
        ('Enlaces y Aplicación', {
            'fields': ('apply_link',)
        }),
        ('Estado y Control', {
            'fields': ('status', 'views_count', 'applications_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    def remote_type(self, obj):
        emoji = {
            'on_site': '🏢',
            'remote': '💻',
            'hybrid': '🏢💻'
        }.get(obj.remote, '📍')
        return f"{emoji} {obj.get_remote_display()}"
    remote_type.short_description = 'Tipo'
    
    def status_badge(self, obj):
        colors = {
            'draft': '#808080',
            'published': '#00AA00',
            'closed': '#FF6600',
            'archived': '#0000FF',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#808080'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def salary_range(self, obj):
        return obj.salary_range()
    salary_range.short_description = 'Rango Salarial'
    
    actions = ['publish_offers', 'close_offers', 'archive_offers']
    
    def publish_offers(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='draft').update(
            status='published',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} ofertas publicadas.')
    publish_offers.short_description = 'Publicar ofertas seleccionadas'
    
    def close_offers(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} ofertas cerradas.')
    close_offers.short_description = 'Cerrar ofertas seleccionadas'
    
    def archive_offers(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} ofertas archivadas.')
    archive_offers.short_description = 'Archivar ofertas seleccionadas'


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'company', 'description')
    readonly_fields = ('created_at',)
