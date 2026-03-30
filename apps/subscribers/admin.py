from django.contrib import admin
from .models import Subscriber, NewsletterSend

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display  = ['email', 'preferred_lang', 'is_active', 'gdpr_consent', 'subscribed_at']
    list_filter   = ['is_active', 'preferred_lang']
    search_fields = ['email']
    ordering      = ['-subscribed_at']

@admin.register(NewsletterSend)
class NewsletterSendAdmin(admin.ModelAdmin):
    list_display    = ['sent_at', 'recipient_count']
    readonly_fields = ['sent_at', 'recipient_count']