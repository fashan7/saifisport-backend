from django.contrib import admin
from .models import MediaFile, ProductImage

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display  = ['filename', 'aspect_ratio', 'file_size_kb', 'uploaded_at']
    list_filter   = ['aspect_ratio']
    search_fields = ['filename', 'alt_text']
    ordering      = ['-uploaded_at']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'media_file', 'order', 'is_primary']
    list_filter  = ['is_primary']