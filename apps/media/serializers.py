from rest_framework import serializers
from .models import MediaFile, ProductImage

class MediaFileSerializer(serializers.ModelSerializer):
    size = serializers.IntegerField(source='file_size_kb', read_only=True)
    created_at = serializers.DateTimeField(source='uploaded_at', read_only=True)
    filename = serializers.CharField(required=False, default='upload')

    class Meta:
        model  = MediaFile
        fields = [
            'id', 'url', 'public_id', 'filename',
            'alt_text', 'title', 'aspect_ratio',
            'size',        
            'width', 'height',
            'created_at',  
        ]
        read_only_fields = ['url', 'public_id', 'size', 'width', 'height', 'created_at']
        
    def create(self, validated_data):
        request = self.context.get('request')
        if not validated_data.get('filename') or validated_data['filename'] == 'upload':
            if request and request.FILES.get('file'):
                validated_data['filename'] = os.path.splitext(
                    request.FILES['file'].name
                )[0]
        return super().create(validated_data)
