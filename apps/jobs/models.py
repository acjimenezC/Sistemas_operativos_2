from django.db import models

class JobOffer(models.Model):
    """Modelo para ofertas laborales"""
    STATUS = (
        ('draft', 'Borrador'),
        ('published', 'Publicada'),
        ('closed', 'Cerrada'),
        ('archived', 'Archivada'),
    )

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    remote = models.CharField(
        max_length=20,
        choices=[
            ('on_site', 'Presencial'),
            ('remote', 'Remoto'),
            ('hybrid', 'Híbrido'),
        ],
        default='on_site'
    )
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    apply_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    views_count = models.IntegerField(default=0)
    applications_count = models.IntegerField(default=0)
    
    # Control - Relación genérica, sin Foreign Key directo para evitar ciclos
    created_by_user_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job Offer'
        verbose_name_plural = 'Job Offers'

    def __str__(self):
        return f"{self.title} - {self.company}"

    def salary_range(self):
        if self.salary_min and self.salary_max:
            return f"{self.salary_min} - {self.salary_max} {self.currency}"
        elif self.salary_min:
            return f"Desde {self.salary_min} {self.currency}"
        elif self.salary_max:
            return f"Hasta {self.salary_max} {self.currency}"
        return "No especificado"


class Job(models.Model):
    """Modelo legado para compatibilidad"""
    STATUS = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=150, blank=True)
    salary = models.CharField(max_length=100, blank=True)
    apply_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.company}"
