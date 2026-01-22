"""
Admin Panel لنظام المحادثات والجلسات
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    ConversationSession, SessionVehicleData, SessionProfileData,
    SessionOffersData, ConversationMessage, StageTransition,
    SessionResult, SessionAnalytics, SessionModificationEvent,
    ConversationStatus, ConversationStage, MessageRole, ModificationEventType
)


class SessionVehicleDataInline(admin.StackedInline):
    """بيانات السيارة inline"""
    model = SessionVehicleData
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at']
    
    fieldsets = (
        ('بيانات السيارة', {
            'fields': ('brand', 'model', 'year', 'value', 'plate_no', 'service_type')
        }),
        ('الحالة', {
            'fields': ('is_complete', 'is_confirmed', 'confirmed_at')
        }),
    )


class SessionProfileDataInline(admin.StackedInline):
    """بيانات العميل inline"""
    model = SessionProfileData
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at']
    
    fieldsets = (
        ('بيانات العميل', {
            'fields': ('national_id', 'birth_date', 'full_name', 'phone', 'email', 'city')
        }),
        ('الحالة', {
            'fields': ('is_complete', 'is_confirmed', 'confirmed_at')
        }),
    )


class SessionOffersDataInline(admin.StackedInline):
    """بيانات العروض inline"""
    model = SessionOffersData
    extra = 0
    readonly_fields = ['shown_at', 'selected_at', 'confirmed_at', 'created_at', 'updated_at']


class SessionResultInline(admin.StackedInline):
    """نتائج الجلسة inline"""
    model = SessionResult
    extra = 0
    readonly_fields = [
        'order_created_at', 'invoice_created_at', 
        'payment_completed_at', 'policy_issued_at',
        'created_at', 'updated_at'
    ]


class SessionAnalyticsInline(admin.StackedInline):
    """تحليلات الجلسة inline"""
    model = SessionAnalytics
    extra = 0
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    """إدارة جلسات المحادثات"""
    
    list_display = [
        'session_id_short', 'user_identifier', 'channel',
        'status_display', 'stage_display', 'message_count',
        'stage_transitions_count', 'created_at', 'last_activity_at'
    ]
    list_filter = ['status', 'current_stage', 'channel', 'created_at']
    search_fields = ['session_id', 'user_identifier']
    readonly_fields = [
        'session_id', 'created_at', 'updated_at', 
        'last_activity_at', 'completed_at'
    ]
    date_hierarchy = 'created_at'
    
    inlines = [
        SessionVehicleDataInline,
        SessionProfileDataInline,
        SessionOffersDataInline,
        SessionResultInline,
        SessionAnalyticsInline,
    ]
    
    fieldsets = (
        ('معلومات الجلسة', {
            'fields': ('session_id', 'user_identifier', 'user', 'channel')
        }),
        ('الحالة والمرحلة', {
            'fields': ('status', 'current_stage', 'previous_stage')
        }),
        ('الإحصائيات', {
            'fields': ('message_count', 'stage_transitions_count')
        }),
        ('الروابط', {
            'fields': ('order',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at', 'last_activity_at', 'completed_at', 'expires_at')
        }),
        ('بيانات إضافية', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def session_id_short(self, obj):
        """عرض معرف الجلسة مختصر"""
        return str(obj.session_id)[:8] + '...'
    session_id_short.short_description = 'معرف الجلسة'
    
    def status_display(self, obj):
        """عرض الحالة بألوان"""
        colors = {
            'active': '#28a745',
            'completed': '#007bff',
            'abandoned': '#ffc107',
            'expired': '#6c757d',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'الحالة'
    
    def stage_display(self, obj):
        """عرض المرحلة"""
        return obj.get_current_stage_display()
    stage_display.short_description = 'المرحلة'


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    """إدارة رسائل المحادثات"""
    
    list_display = [
        'message_id_short', 'session_short', 'role_display',
        'content_short', 'stage_at_message', 'created_at'
    ]
    list_filter = ['role', 'message_type', 'stage_at_message', 'created_at']
    search_fields = ['content', 'session__session_id', 'session__user_identifier']
    readonly_fields = ['message_id', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات الرسالة', {
            'fields': ('message_id', 'session', 'role', 'message_type')
        }),
        ('المحتوى', {
            'fields': ('content', 'stage_at_message')
        }),
        ('البيانات المستخرجة', {
            'fields': ('extracted_data', 'ai_analysis'),
            'classes': ('collapse',)
        }),
        ('بيانات إضافية', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_id_short(self, obj):
        return str(obj.message_id)[:8] + '...'
    message_id_short.short_description = 'معرف الرسالة'
    
    def session_short(self, obj):
        return str(obj.session.session_id)[:8] + '...'
    session_short.short_description = 'الجلسة'
    
    def role_display(self, obj):
        colors = {
            'user': '#28a745',
            'assistant': '#007bff',
            'system': '#6c757d',
        }
        color = colors.get(obj.role, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_display.short_description = 'الدور'
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'المحتوى'


@admin.register(StageTransition)
class StageTransitionAdmin(admin.ModelAdmin):
    """إدارة انتقالات المراحل"""
    
    list_display = [
        'session_short', 'transition_display', 'trigger_type',
        'is_successful', 'duration_seconds', 'created_at'
    ]
    list_filter = ['from_stage', 'to_stage', 'trigger_type', 'is_successful', 'created_at']
    search_fields = ['session__session_id', 'session__user_identifier']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات الانتقال', {
            'fields': ('session', 'from_stage', 'to_stage')
        }),
        ('المحفز', {
            'fields': ('trigger_type', 'trigger_message')
        }),
        ('النتيجة', {
            'fields': ('is_successful', 'failure_reason', 'duration_seconds')
        }),
        ('لقطة البيانات', {
            'fields': ('data_snapshot',),
            'classes': ('collapse',)
        }),
        ('التاريخ', {
            'fields': ('created_at',)
        }),
    )
    
    def session_short(self, obj):
        return str(obj.session.session_id)[:8] + '...'
    session_short.short_description = 'الجلسة'
    
    def transition_display(self, obj):
        return format_html(
            '<span style="color: #6c757d;">{}</span> → <span style="color: #007bff;">{}</span>',
            obj.get_from_stage_display(), obj.get_to_stage_display()
        )
    transition_display.short_description = 'الانتقال'


@admin.register(SessionResult)
class SessionResultAdmin(admin.ModelAdmin):
    """إدارة نتائج الجلسات"""
    
    list_display = [
        'session_short', 'order', 'invoice', 'policy',
        'status_flags', 'total_amount', 'created_at'
    ]
    list_filter = [
        'is_order_created', 'is_invoice_created',
        'is_payment_completed', 'is_policy_issued', 'created_at'
    ]
    search_fields = ['session__session_id', 'session__user_identifier']
    readonly_fields = [
        'order_created_at', 'invoice_created_at',
        'payment_completed_at', 'policy_issued_at',
        'created_at', 'updated_at'
    ]
    
    def session_short(self, obj):
        return str(obj.session.session_id)[:8] + '...'
    session_short.short_description = 'الجلسة'
    
    def status_flags(self, obj):
        flags = []
        if obj.is_order_created:
            flags.append('📦')
        if obj.is_invoice_created:
            flags.append('🧾')
        if obj.is_payment_completed:
            flags.append('💳')
        if obj.is_policy_issued:
            flags.append('📄')
        return ' '.join(flags) if flags else '—'
    status_flags.short_description = 'الحالة'


@admin.register(SessionAnalytics)
class SessionAnalyticsAdmin(admin.ModelAdmin):
    """إدارة تحليلات الجلسات"""
    
    list_display = [
        'session_short', 'total_duration_display',
        'user_messages_count', 'assistant_messages_count',
        'total_modifications', 'drop_off_stage', 'created_at'
    ]
    list_filter = ['drop_off_stage', 'created_at']
    search_fields = ['session__session_id', 'session__user_identifier']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات الجلسة', {
            'fields': ('session',)
        }),
        ('إحصائيات الوقت', {
            'fields': ('total_duration_seconds', 'active_duration_seconds', 'avg_response_time_seconds')
        }),
        ('إحصائيات الرسائل', {
            'fields': ('user_messages_count', 'assistant_messages_count')
        }),
        ('إحصائيات التعديلات', {
            'fields': (
                'total_modifications', 'cancel_count', 'edit_vehicle_count',
                'edit_profile_count', 'change_offer_count', 'go_back_count'
            )
        }),
        ('المراحل', {
            'fields': ('stages_visited', 'time_per_stage', 'drop_off_stage')
        }),
        ('الجودة', {
            'fields': ('ai_confidence_avg', 'extraction_accuracy')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def session_short(self, obj):
        return str(obj.session.session_id)[:8] + '...'
    session_short.short_description = 'الجلسة'
    
    def total_duration_display(self, obj):
        if obj.total_duration_seconds:
            minutes = obj.total_duration_seconds // 60
            seconds = obj.total_duration_seconds % 60
            return f'{minutes}:{seconds:02d}'
        return '—'
    total_duration_display.short_description = 'المدة'


@admin.register(SessionModificationEvent)
class SessionModificationEventAdmin(admin.ModelAdmin):
    """إدارة أحداث التعديل والرجوع والإلغاء"""
    
    list_display = [
        'session_short', 'event_type_display', 'transition_display',
        'is_successful', 'reason_short', 'created_at'
    ]
    list_filter = ['event_type', 'stage_at_event', 'is_successful', 'created_at']
    search_fields = ['session__session_id', 'session__user_identifier', 'reason', 'trigger_message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('معلومات الحدث', {
            'fields': ('session', 'event_type', 'is_successful')
        }),
        ('المراحل', {
            'fields': ('stage_at_event', 'target_stage')
        }),
        ('البيانات', {
            'fields': ('data_before', 'data_after'),
            'classes': ('collapse',)
        }),
        ('التفاصيل', {
            'fields': ('reason', 'trigger_message', 'system_response')
        }),
        ('بيانات إضافية', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def session_short(self, obj):
        return str(obj.session.session_id)[:8] + '...'
    session_short.short_description = 'الجلسة'
    
    def event_type_display(self, obj):
        """عرض نوع الحدث بألوان"""
        colors = {
            'cancel': '#dc3545',
            'edit_vehicle': '#ffc107',
            'edit_profile': '#17a2b8',
            'change_offer': '#6f42c1',
            'go_back': '#6c757d',
            'restart': '#dc3545',
        }
        color = colors.get(obj.event_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_event_type_display()
        )
    event_type_display.short_description = 'نوع الحدث'
    
    def transition_display(self, obj):
        return format_html(
            '<span style="color: #6c757d;">{}</span> → <span style="color: #007bff;">{}</span>',
            obj.get_stage_at_event_display(), obj.get_target_stage_display()
        )
    transition_display.short_description = 'الانتقال'
    
    def reason_short(self, obj):
        if obj.reason:
            return obj.reason[:30] + '...' if len(obj.reason) > 30 else obj.reason
        return '—'
    reason_short.short_description = 'السبب'
