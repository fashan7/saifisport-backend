from rest_framework import serializers
from django.conf import settings
from .models import Category, Product
from apps.media.models import ProductImage, MediaFile

class TranslatedField(serializers.Field):
    """
    Returns the full dict for CMS (admin).
    Returns single resolved string for public frontend (?lang=fr).
    """
    def __init__(self, *args, **kwargs):
        self.public = kwargs.pop('public', False)
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if self.public:
            request = self.context.get('request')
            lang = request.query_params.get('lang', settings.DEFAULT_LANGUAGE) if request else settings.DEFAULT_LANGUAGE
            if lang not in settings.LANGUAGE_CODES:
                lang = settings.DEFAULT_LANGUAGE
            return value.get(lang) or value.get(settings.DEFAULT_LANGUAGE, '')
        return value  # CMS gets the full dict

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError('Expected a JSON object of translations.')
        return data


class CategorySerializer(serializers.ModelSerializer):
    name       = TranslatedField()
    created_at = serializers.DateTimeField(source='id', read_only=True)
    # Category has no created_at — use a stable fallback so frontend doesn't break
    created_at = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'level', 'parent', 'order', 'created_at']

    def get_created_at(self, obj):
        # Category has no timestamp — return a stable placeholder
        return '2026-01-01T00:00:00Z'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Frontend expects name as plain string (fr value) for list views
        request = self.context.get('request')
        if request and not request.user.is_authenticated:
            lang = request.query_params.get('lang', 'fr')
            data['name'] = instance.get_name(lang)
        return data



class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source='media_file.url', read_only=True)

    class Meta:
        model  = ProductImage
        fields = ['id', 'url', 'order', 'is_primary']


class ProductSerializer(serializers.ModelSerializer):
    name        = TranslatedField()
    material    = TranslatedField()
    description = TranslatedField()

    # Frontend expects 'featured', backend field is 'is_featured'
    featured = serializers.BooleanField(source='is_featured')

    # Frontend expects images as flat list of URL strings
    images = serializers.SerializerMethodField()
    # Write-only — accept list of MediaFile IDs when saving
    image_ids   = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )


    category_name    = serializers.SerializerMethodField()
    subcategory_name = serializers.SerializerMethodField()
    type_name        = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'sku', 'name', 'material', 'description',
            'moq', 'featured',
            'category', 'category_name',
            'subcategory', 'subcategory_name',
            'product_type', 'type_name',
            'images', 'image_ids', 'created_at',
        ]

    def get_images(self, obj):
        return [
            {'id': img.media_file.id, 'url': img.media_file.url}
            for img in obj.images.select_related('media_file').all()
            if img.media_file
        ]
        
    def create(self, validated_data):
        image_ids = validated_data.pop('image_ids', [])
        product = super().create(validated_data)
        self._save_images(product, image_ids)
        return product
    
    def update(self, instance, validated_data):
        image_ids = validated_data.pop('image_ids', None)
        product = super().update(instance, validated_data)
        if image_ids is not None:
            instance.images.all().delete()
            self._save_images(product, image_ids)
        return product
    
    def _save_images(self, product, image_ids):
        for i, media_id in enumerate(image_ids):
            try:
                media = MediaFile.objects.get(id=media_id)
                ProductImage.objects.create(
                    product=product,
                    media_file=media,
                    order=i,
                    is_primary=(i == 0)
                )
            except MediaFile.DoesNotExist:
                pass

    def get_category_name(self, obj):
        return obj.category.get_name(self._get_lang()) if obj.category else None

    def get_subcategory_name(self, obj):
        return obj.subcategory.get_name(self._get_lang()) if obj.subcategory else None

    def get_type_name(self, obj):
        return obj.product_type.get_name(self._get_lang()) if obj.product_type else None

    def _get_lang(self):
        request = self.context.get('request')
        from django.conf import settings
        lang = request.query_params.get('lang', settings.DEFAULT_LANGUAGE) if request else settings.DEFAULT_LANGUAGE
        return lang if lang in settings.LANGUAGE_CODES else settings.DEFAULT_LANGUAGE