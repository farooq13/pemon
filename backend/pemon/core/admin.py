from django.contrib import admin

from .models import AppVersion, AuditLog, SystemConfiguration


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for viewing audit logs."""
    
    list_display = [
        'id',
        'user',
        'action',
        'model_name',
        'object_id',
        'ip_address',
        'created_at',
    ]
    list_filter = [
        'action',
        'model_name',
        'created_at',
    ]
    search_fields = [
        'user__email',
        'model_name',
        'object_id',
        'ip_address',
    ]
    readonly_fields = [
        'id',
        'user',
        'action',
        'model_name',
        'object_id',
        'changes',
        'ip_address',
        'user_agent',
        'metadata',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        """Disable adding audit logs through admin."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting audit logs through admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing audit logs through admin."""
        return False


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for system configurations."""
    
    list_display = [
        'key',
        'value_preview',
        'is_active',
        'updated_at',
    ]
    list_filter = [
        'is_active',
        'created_at',
    ]
    search_fields = [
        'key',
        'description',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Configuration', {
            'fields': ('key', 'value', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def value_preview(self, obj):
        """Show preview of value (first 50 characters)."""
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    """Admin interface for app versions."""
    
    list_display = [
        'platform',
        'version_number',
        'build_number',
        'is_force_update',
        'created_at',
    ]
    list_filter = [
        'platform',
        'is_force_update',
        'created_at',
    ]
    search_fields = [
        'version_number',
        'release_notes',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Version Information', {
            'fields': (
                'platform',
                'version_number',
                'build_number',
                'minimum_supported_version',
            )
        }),
        ('Update Settings', {
            'fields': (
                'is_force_update',
                'download_url',
            )
        }),
        ('Release Notes', {
            'fields': ('release_notes',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )