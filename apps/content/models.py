from django.db import models
from django.conf import settings

def translated_default():
    return {code: '' for code in settings.LANGUAGE_CODES}


class Page(models.Model):
    slug        = models.SlugField(max_length=100, unique=True)
    title       = models.JSONField(default=translated_default)
    content     = models.JSONField(default=translated_default)
    is_published = models.BooleanField(default=False)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.slug


class Banner(models.Model):
    title        = models.JSONField(default=translated_default)
    subtitle     = models.JSONField(default=translated_default)
    button_text  = models.JSONField(default=translated_default)
    image_url    = models.URLField(max_length=500, blank=True)
    button_link  = models.CharField(max_length=200, blank=True)
    is_active    = models.BooleanField(default=True)
    order        = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        titles = self.title
        return titles.get('fr', '') or str(self.id)


class EmailTemplate(models.Model):
    class TemplateType(models.TextChoices):
        TRANSACTIONAL = 'transactional', 'Transactional'
        NOTIFICATION  = 'notification',  'Notification'
        MARKETING     = 'marketing',     'Marketing'

    name       = models.CharField(max_length=100, unique=True)
    type       = models.CharField(max_length=20, choices=TemplateType.choices)
    subject    = models.JSONField(default=translated_default)
    body       = models.JSONField(default=translated_default)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name