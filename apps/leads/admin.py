from django.contrib import admin
from .models import Lead

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display  = ['club_name', 'full_name', 'email', 'country', 'category', 'quantity', 'status', 'priority', 'created_at']
    list_filter   = ['status', 'priority', 'country']
    search_fields = ['club_name', 'email', 'full_name']
    ordering      = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']