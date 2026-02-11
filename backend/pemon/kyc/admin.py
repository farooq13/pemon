from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import KYC, KYCDocument
from .services import KYCService


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    """Admin interface for KYC verification."""
    
    list_display = [
        'user_email',
        'tier_badge',
        'status_badge',
        'has_documents',
        'submitted_at',
        'verified_at',
        'action_buttons',
    ]
    
    list_filter = [
        'tier',
        'status',
        'submitted_at',
        'verified_at',
    ]
    
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'user__phone_number',
        'bvn',
        'nin',
    ]
    
    readonly_fields = [
        'id',
        'user',
        'submitted_at',
        'verified_by',
        'verified_at',
        'created_at',
        'updated_at',
        'document_preview',
        'selfie_preview',
        'tier_limits_display',
    ]
    
    date_hierarchy = 'submitted_at'
    
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('User Information', {
            'fields': (
                'id',
                'user',
                'tier',
                'status',
            )
        }),
        ('Personal Information', {
            'fields': (
                'bvn',
                'nin',
                'date_of_birth',
                'address',
                'city',
                'state',
            )
        }),
        ('Identity Documents', {
            'fields': (
                'id_type',
                'id_number',
                'document_preview',
                'selfie_preview',
            )
        }),
        ('Verification Details', {
            'fields': (
                'verified_by',
                'verified_at',
                'rejection_reason',
            )
        }),
        ('Tier Limits', {
            'fields': ('tier_limits_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'submitted_at',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'approve_tier_1',
        'approve_tier_2',
        'approve_tier_3',
        'reject_kyc',
    ]
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def tier_badge(self, obj):
        """Display tier as colored badge."""
        colors = {
            0: '#6c757d',  # Gray
            1: '#17a2b8',  # Blue
            2: '#ffc107',  # Yellow
            3: '#28a745',  # Green
        }
        
        color = colors.get(obj.tier, '#6c757d')
        tier_name = obj.get_tier_limits()['name']
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; '
            'border-radius: 4px; font-size: 11px; font-weight: 600;">'
            'Tier {} - {}</span>',
            color, obj.tier, tier_name
        )
    tier_badge.short_description = 'Tier'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'PENDING': '#ffc107',  # Yellow
            'UNDER_REVIEW': '#17a2b8',  # Blue
            'APPROVED': '#28a745',  # Green
            'REJECTED': '#dc3545',  # Red
            'EXPIRED': '#6c757d',  # Gray
        }
        
        color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 10px; '
            'border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_documents(self, obj):
        """Show if documents are uploaded."""
        check_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" '
            'aria-hidden="true" focusable="false" style="vertical-align:middle; margin-right:4px;">'
            '<path d="M2 8l3 3 9-9" stroke="#28a745" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg>'
        )
        cross_svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" '
            'aria-hidden="true" focusable="false" style="vertical-align:middle; margin-right:4px;">'
            '<path d="M2 2l12 12M14 2L2 14" stroke="#dc3545" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg>'
        )

        has_id = check_svg if obj.id_document else cross_svg
        has_selfie = check_svg if obj.selfie else cross_svg

        return format_html(
            '<span title="ID Document">{}</span> '
            '<span title="Selfie">{}</span>',
            mark_safe(has_id), mark_safe(has_selfie)
        )
    has_documents.short_description = 'Documents'
    
    def document_preview(self, obj):
        """Show ID document preview."""
        if obj.id_document:
            if obj.id_document.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; padding: 5px;"/>'
                    '</a>',
                    obj.id_document.url,
                    obj.id_document.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank" class="button">View Document ({})</a>',
                    obj.id_document.url,
                    obj.id_document.name.split('.')[-1].upper()
                )
        return 'No document uploaded'
    document_preview.short_description = 'ID Document Preview'
    
    def selfie_preview(self, obj):
        """Show selfie preview."""
        if obj.selfie:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 200px; max-height: 200px; border: 1px solid #ddd; padding: 5px;"/>'
                '</a>',
                obj.selfie.url,
                obj.selfie.url
            )
        return 'No selfie uploaded'
    selfie_preview.short_description = 'Selfie Preview'
    
    def tier_limits_display(self, obj):
        """Display tier limits information."""
        limits = obj.get_tier_limits()
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f8f9fa;"><th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Limit Type</th><th style="padding: 8px; text-align: left; border: 1px solid #dee2e6;">Amount</th></tr>'
        html += f'<tr><td style="padding: 8px; border: 1px solid #dee2e6;">Daily Limit</td><td style="padding: 8px; border: 1px solid #dee2e6;">₦{limits["daily_limit"]:,.2f}</td></tr>'
        html += f'<tr><td style="padding: 8px; border: 1px solid #dee2e6;">Single Transaction</td><td style="padding: 8px; border: 1px solid #dee2e6;">₦{limits["single_transaction_limit"]:,.2f}</td></tr>'
        html += f'<tr><td style="padding: 8px; border: 1px solid #dee2e6;">Total Balance</td><td style="padding: 8px; border: 1px solid #dee2e6;">₦{limits["total_balance_limit"]:,.2f}</td></tr>'
        html += f'<tr><td style="padding: 8px; border: 1px solid #dee2e6;">Monthly Limit</td><td style="padding: 8px; border: 1px solid #dee2e6;">₦{limits["monthly_limit"]:,.2f}</td></tr>'
        html += '</table>'
        
        return mark_safe(html)
    tier_limits_display.short_description = 'Transaction Limits'
    
    def action_buttons(self, obj):
        """Display action buttons."""
        if obj.status == KYC.Status.PENDING:
            return format_html(
                '<a class="button" href="/admin/kyc/kyc/{}/change/">Review</a>',
                obj.pk
            )
        return '-'
    action_buttons.short_description = 'Actions'
    
    # Admin Actions
    def approve_tier_1(self, request, queryset):
        """Approve selected KYC applications as Tier 1."""
        count = 0
        for kyc in queryset.filter(status__in=[KYC.Status.PENDING, KYC.Status.UNDER_REVIEW]):
            try:
                KYCService.approve_kyc(kyc.id, request.user, tier=1)
                count += 1
            except Exception as e:
                self.message_user(request, f'Error approving {kyc.user.email}: {e}', level='ERROR')
        
        self.message_user(request, f'Successfully approved {count} KYC applications as Tier 1.')
    approve_tier_1.short_description = 'Approve as Tier 1'
    
    def approve_tier_2(self, request, queryset):
        """Approve selected KYC applications as Tier 2."""
        count = 0
        for kyc in queryset.filter(status__in=[KYC.Status.PENDING, KYC.Status.UNDER_REVIEW]):
            try:
                KYCService.approve_kyc(kyc.id, request.user, tier=2)
                count += 1
            except Exception as e:
                self.message_user(request, f'Error approving {kyc.user.email}: {e}', level='ERROR')
        
        self.message_user(request, f'Successfully approved {count} KYC applications as Tier 2.')
    approve_tier_2.short_description = 'Approve as Tier 2'
    
    def approve_tier_3(self, request, queryset):
        """Approve selected KYC applications as Tier 3."""
        count = 0
        for kyc in queryset.filter(status__in=[KYC.Status.PENDING, KYC.Status.UNDER_REVIEW]):
            try:
                KYCService.approve_kyc(kyc.id, request.user, tier=3)
                count += 1
            except Exception as e:
                self.message_user(request, f'Error approving {kyc.user.email}: {e}', level='ERROR')
        
        self.message_user(request, f'Successfully approved {count} KYC applications as Tier 3.')
    approve_tier_3.short_description = 'Approve as Tier 3'
    
    def reject_kyc(self, request, queryset):
        """Reject selected KYC applications."""
        # This would ideally show a form to enter rejection reason
        # For now, using a generic message
        count = 0
        for kyc in queryset.filter(status__in=[KYC.Status.PENDING, KYC.Status.UNDER_REVIEW]):
            try:
                KYCService.reject_kyc(
                    kyc.id,
                    request.user,
                    reason='Documents do not meet requirements. Please resubmit with valid documents.'
                )
                count += 1
            except Exception as e:
                self.message_user(request, f'Error rejecting {kyc.user.email}: {e}', level='ERROR')
        
        self.message_user(request, f'Successfully rejected {count} KYC applications.')
    reject_kyc.short_description = 'Reject KYC'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of KYC records."""
        return False


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    """Admin interface for additional KYC documents."""
    
    list_display = [
        'id',
        'kyc_user',
        'document_type',
        'uploaded_at',
    ]
    
    list_filter = [
        'document_type',
        'created_at',
    ]
    
    search_fields = [
        'kyc__user__email',
        'document_type',
        'notes',
    ]
    
    readonly_fields = [
        'id',
        'kyc',
        'created_at',
        'updated_at',
        'document_preview',
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                'id',
                'kyc',
                'document_type',
                'document_preview',
                'notes',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def kyc_user(self, obj):
        """Display KYC user email."""
        return obj.kyc.user.email
    kyc_user.short_description = 'User'
    kyc_user.admin_order_field = 'kyc__user__email'
    
    def uploaded_at(self, obj):
        """Display upload timestamp."""
        return obj.created_at
    uploaded_at.short_description = 'Uploaded At'
    uploaded_at.admin_order_field = 'created_at'
    
    def document_preview(self, obj):
        """Show document preview."""
        if obj.document:
            if obj.document.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; padding: 5px;"/>'
                    '</a>',
                    obj.document.url,
                    obj.document.url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank" class="button">View Document ({})</a>',
                    obj.document.url,
                    obj.document.name.split('.')[-1].upper()
                )
        return 'No document'
    document_preview.short_description = 'Document Preview'