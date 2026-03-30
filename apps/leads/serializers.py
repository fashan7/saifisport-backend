from rest_framework import serializers
from .models import Lead

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Lead
        fields = [
            'id', 'club_name', 'full_name', 'vat_number',
            'email', 'phone', 'country', 'country_code',
            'category', 'quantity', 'custom_branding', 'logo_file',
            'browser_language', 'notes', 'status', 'priority',
            'lead_type', 'reference_image', 'preferred_material',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']