from django.db import models
from django.conf import settings

def translated_default():
    return {code: '' for code in settings.LANGUAGE_CODES}


class SiteSettings(models.Model):
    """Singleton — always only one row (id=1)."""

    # General
    contact_email  = models.EmailField(blank=True)
    whatsapp       = models.CharField(max_length=30, blank=True)
    phone_numbers  = models.CharField(max_length=200, blank=True)
    office_address = models.TextField(blank=True)

    # SEO (translatable)
    meta_title       = models.JSONField(default=translated_default)
    meta_description = models.JSONField(default=translated_default)

    # Holiday mode
    holiday_mode    = models.BooleanField(default=False)
    holiday_message = models.JSONField(default=translated_default)

    # Integrations
    active_translation_engine = models.CharField(
        max_length=30,
        choices=[('lovable', 'Lovable AI'), ('deepl', 'DeepL'), ('google', 'Google Translate')],
        default='lovable'
    )
    deepl_api_key          = models.CharField(max_length=200, blank=True)
    google_translate_key   = models.CharField(max_length=200, blank=True)
    calendly_url           = models.URLField(blank=True)
    zoom_url               = models.URLField(blank=True)
    primary_meeting_method = models.CharField(
        max_length=10,
        choices=[('calendly', 'Calendly'), ('zoom', 'Zoom')],
        default='calendly'
    )

    class Meta:
        verbose_name = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1  # Always enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Site Settings'