from rest_framework import serializers
from .models import SiteSettings


class PhoneNumbersField(serializers.Field):
    """Converts between comma-separated DB string and JSON array."""
    def to_representation(self, value):
        if not value:
            return []
        return [p.strip() for p in value.split(',') if p.strip()]

    def to_internal_value(self, data):
        if isinstance(data, list):
            return ', '.join(str(p).strip() for p in data if str(p).strip())
        if isinstance(data, str):
            return data
        return ''


class TranslatableField(serializers.Field):
    """
    Read:  authenticated → full dict  |  public → resolved string
    Write: accepts dict or plain string
    """
    def to_representation(self, value):
        request = self.context.get('request')
        is_admin = request and request.user and request.user.is_authenticated
        if is_admin:
            if isinstance(value, dict):
                return value
            return {'fr': value or ''}
        # Public — resolve to string
        lang = request.query_params.get('lang', 'fr') if request else 'fr'
        if isinstance(value, dict):
            return value.get(lang) or value.get('fr', '')
        return value or ''

    def to_internal_value(self, data):
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            return {'fr': data}
        return {}


class SiteSettingsSerializer(serializers.ModelSerializer):
    # Rename whatsapp → whatsapp_number for frontend compatibility
    whatsapp_number  = serializers.CharField(
        source='whatsapp', allow_blank=True, required=False
    )
    # Proper read/write for phone numbers
    phone_numbers    = PhoneNumbersField(required=False)
    # Proper read/write for translatable fields
    holiday_message  = TranslatableField(required=False)
    meta_title       = TranslatableField(required=False)
    meta_description = TranslatableField(required=False)

    class Meta:
        model  = SiteSettings
        fields = [
            'office_address',
            'contact_email',
            'whatsapp_number',
            'phone_numbers',
            'holiday_mode',
            'holiday_message',
            'meta_title',
            'meta_description',
            'active_translation_engine',
            'calendly_url',
            'zoom_url',
            'primary_meeting_method',
        ]
        extra_kwargs = {
            'deepl_api_key':        {'write_only': True},
            'google_translate_key': {'write_only': True},
        }