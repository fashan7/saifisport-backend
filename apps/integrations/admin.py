from django.contrib import admin
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['contact_email', 'holiday_mode', 'active_translation_engine']

    def has_add_permission(self, request):
        # Prevent creating more than one row
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # Never delete the singleton