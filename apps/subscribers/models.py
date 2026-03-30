from django.db import models
import uuid

class Subscriber(models.Model):
    email           = models.EmailField(unique=True)
    preferred_lang  = models.CharField(max_length=5, default='fr')
    is_active       = models.BooleanField(default=True)
    gdpr_consent    = models.BooleanField(default=False)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subscribed_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class NewsletterSend(models.Model):
    subject          = models.JSONField()
    body             = models.JSONField()
    sent_at          = models.DateTimeField(auto_now_add=True)
    recipient_count  = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-sent_at']