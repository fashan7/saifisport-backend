from django.contrib import admin
from .models import Page, Banner, EmailTemplate

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display  = ['slug', 'get_title_fr', 'is_published', 'updated_at']
    list_filter   = ['is_published']
    search_fields = ['slug']

    def get_title_fr(self, obj):
        return obj.title.get('fr', '-')
    get_title_fr.short_description = 'Title (FR)'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display  = ['get_title_fr', 'is_active', 'order']
    list_filter   = ['is_active']
    ordering      = ['order']

    def get_title_fr(self, obj):
        return obj.title.get('fr', '-')
    get_title_fr.short_description = 'Title (FR)'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display  = ['name', 'type', 'updated_at']
    list_filter   = ['type']
    search_fields = ['name']