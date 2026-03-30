from rest_framework import serializers
from .models import Subscriber, NewsletterSend


class SubscriberSerializer(serializers.ModelSerializer):
    # Frontend expects status: "active" | "unsubscribed"
    status = serializers.SerializerMethodField()
    
    class Meta:
        model  = Subscriber
        fields = ['id', 'email', 'status', 'subscribed_at']
        read_only_fields = ['subscribed_at']

    def get_status(self, obj):
        return 'active' if obj.is_active else 'unsubscribed'

    def to_internal_value(self, data):
        # Accept GDPR consent from frontend subscribe form
        internal = super().to_internal_value(data)
        internal['gdpr_consent'] = True   # implied by form submission
        internal['is_active'] = True
        return internal


class NewsletterSendSerializer(serializers.ModelSerializer):
    class Meta:
        model  = NewsletterSend
        fields = ['id', 'subject', 'body', 'sent_at', 'recipient_count']
        read_only_fields = ['sent_at', 'recipient_count']