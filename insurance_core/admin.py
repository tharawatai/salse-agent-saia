"""
Admin Panel لنظام التأمين
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    User, Vehicle, InsuranceCompany, InsuranceService,
    InsuranceOffer, InsuranceOrder, Invoice, Payment, Policy
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """إدارة المستخدمين"""
    list_display = ['user_code', 'get_full_name', 'national_id', 'phone', 'city', 'age', 'created_at']
    search_fields = ['user_code', 'national_id', 'phone', 'first_name', 'last_name', 'email']
    list_filter = ['city', 'age', 'created_at']
    readonly_fields = ['user_code', 'age', 'created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('user_code', 'username', 'email', 'first_name', 'last_name')
        }),
        ('معلومات شخصية', {
            'fields': ('national_id', 'birth_date', 'age', 'phone', 'city')
        }),
        ('الصلاحيات', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at', 'last_login')
        }),
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """إدارة المركبات"""
    list_display = ['plate_no', 'user', 'brand', 'model', 'model_year', 'vehicle_value', 'created_at']
    search_fields = ['plate_no', 'brand', 'model', 'user__national_id', 'user__phone']
    list_filter = ['brand', 'model_year', 'created_at']
    autocomplete_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات المركبة', {
            'fields': ('user', 'plate_no', 'brand', 'model', 'model_year', 'vehicle_value')
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    """إدارة شركات التأمين"""
    list_display = ['company_code', 'name_ar', 'name_en', 'rating_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'rating_score']
    search_fields = ['name_ar', 'name_en', 'company_code']
    readonly_fields = ['created_at', 'updated_at']
    
    def rating_display(self, obj):
        """عرض التقييم بالنجوم"""
        stars = '⭐' * int(obj.rating_score)
        return format_html(f'{stars} ({obj.rating_score})')
    rating_display.short_description = 'التقييم'


@admin.register(InsuranceService)
class InsuranceServiceAdmin(admin.ModelAdmin):
    """إدارة خدمات التأمين"""
    list_display = ['service_code', 'name_ar', 'name_en', 'service_type']
    list_filter = ['service_type']
    search_fields = ['name_ar', 'name_en', 'service_code']


@admin.register(InsuranceOffer)
class InsuranceOfferAdmin(admin.ModelAdmin):
    """إدارة عروض التأمين"""
    list_display = [
        'offer_code', 'company', 'service', 'coverage_type', 
        'price_base', 'min_age', 'max_age', 'is_active', 'created_at'
    ]
    list_filter = ['company', 'service', 'coverage_type', 'is_active', 'created_at']
    search_fields = ['offer_code', 'company__name_ar', 'service__name_ar']
    autocomplete_fields = ['company', 'service']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('offer_code', 'company', 'service', 'coverage_type', 'is_active')
        }),
        ('المتطلبات', {
            'fields': ('min_age', 'max_age', 'min_vehicle_year', 'max_vehicle_value')
        }),
        ('التسعير', {
            'fields': ('price_base', 'njm_discount_pct', 'vat_rate')
        }),
        ('المزايا والإضافات', {
            'fields': ('deductible_options', 'included_features_json', 'optional_addons_json'),
            'classes': ('collapse',)
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(InsuranceOrder)
class InsuranceOrderAdmin(admin.ModelAdmin):
    """إدارة طلبات التأمين"""
    list_display = [
        'order_code', 'user', 'offer', 'vehicle', 
        'total_price', 'status_display', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'has_njm_discount']
    search_fields = ['order_code', 'user__national_id', 'user__phone']
    autocomplete_fields = ['user', 'offer', 'vehicle']
    readonly_fields = ['order_code', 'created_at', 'updated_at']
    
    def status_display(self, obj):
        """عرض الحالة بألوان"""
        colors = {
            'draft': 'gray',
            'awaiting_confirmation': 'orange',
            'pending_payment': 'blue',
            'paid': 'green',
            'policy_issued': 'darkgreen',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'الحالة'
    
    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('order_code', 'user', 'offer', 'vehicle', 'status')
        }),
        ('التسعير', {
            'fields': ('total_price', 'has_njm_discount', 'selected_deductible', 'selected_addons')
        }),
        ('ملاحظات', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('تواريخ', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """إدارة الفواتير"""
    list_display = [
        'invoice_no', 'order', 'amount', 'status_display', 
        'expires_at', 'paid_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = ['invoice_no', 'order__order_code']
    readonly_fields = ['invoice_no', 'created_at', 'is_expired']
    
    def status_display(self, obj):
        """عرض الحالة بألوان"""
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'expired': 'red',
            'cancelled': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'الحالة'
    
    fieldsets = (
        ('معلومات الفاتورة', {
            'fields': ('invoice_no', 'order', 'amount', 'status')
        }),
        ('التواريخ', {
            'fields': ('expires_at', 'paid_at', 'created_at', 'is_expired')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """إدارة المدفوعات"""
    list_display = [
        'transaction_ref', 'invoice', 'amount', 'payment_method', 
        'status_display', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_ref', 'invoice__invoice_no']
    readonly_fields = ['created_at']
    
    def status_display(self, obj):
        """عرض الحالة بألوان"""
        colors = {
            'pending': 'gray',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'orange',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'الحالة'
    
    fieldsets = (
        ('معلومات الدفع', {
            'fields': ('invoice', 'transaction_ref', 'amount', 'payment_method', 'status')
        }),
        ('استجابة البوابة', {
            'fields': ('gateway_response',),
            'classes': ('collapse',)
        }),
        ('تواريخ', {
            'fields': ('created_at', 'completed_at')
        }),
    )


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    """إدارة وثائق التأمين"""
    list_display = [
        'policy_no', 'order', 'start_date', 'end_date', 
        'is_active_display', 'days_remaining', 'issued_at'
    ]
    list_filter = ['start_date', 'end_date', 'issued_at']
    search_fields = ['policy_no', 'order__order_code']
    readonly_fields = ['policy_no', 'issued_at', 'is_active', 'days_remaining']
    
    def is_active_display(self, obj):
        """عرض حالة الوثيقة"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ سارية</span>')
        return format_html('<span style="color: red;">✗ منتهية</span>')
    is_active_display.short_description = 'الحالة'
    
    fieldsets = (
        ('معلومات الوثيقة', {
            'fields': ('policy_no', 'order', 'pdf_url')
        }),
        ('الفترة الزمنية', {
            'fields': ('start_date', 'end_date', 'is_active', 'days_remaining')
        }),
        ('تواريخ', {
            'fields': ('issued_at',)
        }),
    )


# تخصيص Admin Site
admin.site.site_header = "نظام SAIA للتأمين الذكي"
admin.site.site_title = "SAIA Admin"
admin.site.index_title = "لوحة التحكم"
