from rest_framework import serializers
from .models import MediaFile, ProductImage

class MediaFileSerializer(serializers.ModelSerializer):
    # Frontend expects 'size', backend field is 'file_size_kb'
    size = serializers.IntegerField(source='file_size_kb', read_only=True)

    # Frontend expects 'created_at', backend field is 'uploaded_at'
    created_at = serializers.DateTimeField(source='uploaded_at', read_only=True)

    class Meta:
        model  = MediaFile
        fields = [
            'id', 'url', 'public_id', 'filename',
            'alt_text', 'aspect_ratio',
            'size',        # mapped from file_size_kb
            'width', 'height',
            'created_at',  # mapped from uploaded_at
        ]
        read_only_fields = ['url', 'public_id', 'size', 'width', 'height', 'created_at']
