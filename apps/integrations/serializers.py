from rest_framework import serializers
from .models import SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    whatsapp_number = serializers.CharField(source='whatsapp', allow_blank=True)

    # Frontend expects phone_numbers as a list, backend stores comma-separated string
    phone_numbers = serializers.SerializerMethodField()

    # Frontend expects holiday_message as a plain string (fr value)
    # but CMS admin gets the full dict — handled below
    holiday_message = serializers.SerializerMethodField()
    
    class Meta:
        model  = SiteSettings
        fields = [
            'office_address', 'contact_email',
            'whatsapp_number', 'phone_numbers',
            'holiday_mode', 'holiday_message',
            'meta_title', 'meta_description',
            'active_translation_engine',
            'calendly_url', 'zoom_url', 'primary_meeting_method',
        ]
        extra_kwargs = {
            'deepl_api_key':        {'write_only': True},
            'google_translate_key': {'write_only': True},
        }

    def get_phone_numbers(self, obj):
        # Store as comma-separated, return as list
        if not obj.phone_numbers:
            return []
        return [p.strip() for p in obj.phone_numbers.split(',') if p.strip()]

    def get_holiday_message(self, obj):
        request = self.context.get('request')
        # Authenticated CMS gets full dict for translation tabs
        if request and request.user and request.user.is_authenticated:
            return obj.holiday_message
        # Public frontend gets resolved string
        lang = request.query_params.get('lang', 'fr') if request else 'fr'
        return obj.holiday_message.get(lang) or obj.holiday_message.get('fr', '')

    def to_internal_value(self, data):
        # Convert phone_numbers list back to comma-separated string on save
        data = data.copy()
        if 'phone_numbers' in data and isinstance(data['phone_numbers'], list):
            data['phone_numbers'] = ', '.join(data['phone_numbers'])
        if 'whatsapp_number' in data:
            data['whatsapp'] = data.pop('whatsapp_number')
        return super().to_internal_value(data)