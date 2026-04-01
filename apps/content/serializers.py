from rest_framework import serializers
from django.conf import settings
from .models import Page, Banner, EmailTemplate


class TranslatedField(serializers.Field):
    def to_representation(self, value):
        return value if isinstance(value, dict) else {}

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError('Expected a translations object.')
        return data


class PageSerializer(serializers.ModelSerializer):
    title   = TranslatedField()
    content = TranslatedField()

    class Meta:
        model  = Page
        fields = ['id', 'slug', 'title', 'content', 'is_published', 'updated_at']


class BannerSerializer(serializers.ModelSerializer):
    title       = TranslatedField()
    subtitle    = TranslatedField()
    button_text = TranslatedField()

    class Meta:
        model  = Banner
        fields = [
            'id', 'title', 'subtitle', 'button_text',
            'image_url', 'button_link', 'is_active', 'order'
        ]


class EmailTemplateSerializer(serializers.ModelSerializer):
    subject = TranslatedField()
    body    = TranslatedField()

    class Meta:
        model  = EmailTemplate
        fields = ['id', 'name', 'type', 'subject', 'body', 'updated_at']