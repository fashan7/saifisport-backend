from django.db import models

class LeadType(models.TextChoices):
    STANDARD = 'standard', 'Standard Quote'
    CUSTOM   = 'custom',   'Custom Development'

class Lead(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        CONTACTED = 'contacted', 'Contacted'
        QUALIFIED = 'qualified', 'Qualified'
        CLOSED    = 'closed',    'Closed'
        LOST      = 'lost',      'Lost'

    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH   = 'high',   'High'

    club_name      = models.CharField(max_length=200)
    club_name        = models.CharField(max_length=200)
    full_name        = models.CharField(max_length=200, blank=True)
    vat_number       = models.CharField(max_length=50, blank=True)
    email            = models.EmailField()
    phone            = models.CharField(max_length=30, blank=True)
    country          = models.CharField(max_length=100)
    country_code     = models.CharField(max_length=10, blank=True)  # FR, DE, ES...
    category         = models.CharField(max_length=100)
    quantity         = models.CharField(max_length=50)
    custom_branding  = models.BooleanField(default=False)
    logo_file        = models.FileField(upload_to='logos/', null=True, blank=True)
    browser_language = models.CharField(max_length=10, blank=True)
    lead_type          = models.CharField(
        max_length=20, choices=LeadType.choices, default=LeadType.STANDARD
    )
    reference_image    = models.FileField(
        upload_to='custom-requests/', null=True, blank=True
    )
    preferred_material = models.CharField(max_length=50, blank=True)
    
    notes    = models.TextField(blank=True)
    status   = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.club_name} ({self.country}) — {self.status}"