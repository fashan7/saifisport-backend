from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['get_name_fr', 'slug', 'level', 'parent', 'order']
    list_filter   = ['level']
    search_fields = ['slug']
    ordering      = ['level', 'order']

    def get_name_fr(self, obj):
        return obj.name.get('fr', '-')
    get_name_fr.short_description = 'Name (FR)'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['sku', 'get_name_fr', 'category', 'moq', 'is_featured', 'created_at']
    list_filter   = ['is_featured', 'category']
    search_fields = ['sku']
    ordering      = ['-created_at']

    def get_name_fr(self, obj):
        return obj.name.get('fr', '-')
    get_name_fr.short_description = 'Name (FR)'