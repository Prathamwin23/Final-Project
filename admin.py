from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Client, Assignment, LocationLog, ImportLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_active_agent', 'last_location_update', 'location_link']
    list_filter = ['user_type', 'is_active_agent', 'date_joined']
    search_fields = ['username', 'email', 'phone_number']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('User Details', {'fields': ('user_type', 'phone_number', 'is_active_agent')}),
        ('Location', {'fields': ('current_latitude', 'current_longitude', 'last_location_update')}),
    )
    
    def location_link(self, obj):
        if obj.current_latitude and obj.current_longitude:
            return format_html(
                '<a href="https://www.google.com/maps?q={},{}" target="_blank">View on Map</a>',
                obj.current_latitude, obj.current_longitude
            )
        return "No location"
    location_link.short_description = 'Location'

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'priority', 'status', 'created_at', 'location_link']
    list_filter = ['priority', 'status', 'created_at']
    search_fields = ['name', 'phone', 'email', 'address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Client Information', {
            'fields': ['name', 'phone', 'email', 'address']
        }),
        ('Location', {
            'fields': ['latitude', 'longitude']
        }),
        ('Assignment Details', {
            'fields': ['priority', 'status', 'notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def location_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://www.google.com/maps?q={},{}" target="_blank">View on Map</a>',
                obj.latitude, obj.longitude
            )
        return "No location"
    location_link.short_description = 'Location'
    
    actions = ['mark_as_pending', 'mark_as_completed']
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
        self.message_user(request, f"{queryset.count()} clients marked as pending.")
    mark_as_pending.short_description = "Mark selected clients as pending"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} clients marked as completed.")
    mark_as_completed.short_description = "Mark selected clients as completed"

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['agent', 'client', 'status', 'assigned_at', 'duration']
    list_filter = ['status', 'assigned_at', 'agent']
    search_fields = ['agent__username', 'client__name']
    readonly_fields = ['assigned_at', 'accepted_at', 'started_at', 'completed_at', 'duration']
    
    fieldsets = [
        ('Assignment Details', {
            'fields': ['agent', 'client', 'status']
        }),
        ('Timestamps', {
            'fields': ['assigned_at', 'accepted_at', 'started_at', 'completed_at', 'duration']
        }),
        ('Notes', {
            'fields': ['notes'],
            'classes': ['collapse']
        }),
    ]
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            duration = obj.completed_at - obj.started_at
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m"
        return "Not completed"
    duration.short_description = 'Duration'
    
    actions = ['reassign_to_pending']
    
    def reassign_to_pending(self, request, queryset):
        for assignment in queryset:
            assignment.client.status = 'pending'
            assignment.client.save()
        queryset.delete()
        self.message_user(request, f"{queryset.count()} assignments deleted and clients marked as pending.")
    reassign_to_pending.short_description = "Delete assignments and mark clients as pending"

@admin.register(LocationLog)
class LocationLogAdmin(admin.ModelAdmin):
    list_display = ['agent', 'latitude', 'longitude', 'timestamp', 'accuracy']
    list_filter = ['agent', 'timestamp']
    search_fields = ['agent__username']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        return False  # Prevent manual addition of location logs

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'uploaded_by', 'upload_time', 'total_rows', 'successful_imports', 'failed_imports']
    list_filter = ['upload_time', 'uploaded_by']
    search_fields = ['file_name', 'uploaded_by__username']
    readonly_fields = ['upload_time']
    
    fieldsets = [
        ('Import Details', {
            'fields': ['file_name', 'uploaded_by', 'upload_time']
        }),
        ('Results', {
            'fields': ['total_rows', 'successful_imports', 'failed_imports']
        }),
        ('Errors', {
            'fields': ['error_details'],
            'classes': ['collapse']
        }),
    ]
    
    def has_add_permission(self, request):
        return False  # Prevent manual addition of import logs

# Customize admin site
admin.site.site_header = "Field Operations Management"
admin.site.site_title = "Field Ops Admin"
admin.site.index_title = "Welcome to Field Operations Management System"