"""
Custom Model Managers لتحسين الاستعلامات
"""
from django.db import models
from django.db.models import Q, Prefetch


class ActiveManager(models.Manager):
    """Manager للعناصر النشطة فقط"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class InsuranceOfferManager(models.Manager):
    """Manager مخصص لعروض التأمين"""
    
    def active(self):
        """العروض النشطة فقط"""
        return self.filter(is_active=True)
    
    def for_user_age(self, age):
        """العروض المناسبة لعمر معين"""
        return self.filter(
            min_age__lte=age,
            max_age__gte=age,
            is_active=True
        )
    
    def for_vehicle_year(self, year):
        """العروض المناسبة لسنة مركبة معينة"""
        return self.filter(
            min_vehicle_year__lte=year,
            is_active=True
        )
    
    def comprehensive_offers(self):
        """عروض التأمين الشامل"""
        return self.filter(
            coverage_type='comprehensive',
            is_active=True
        )
    
    def with_company_details(self):
        """جلب العروض مع تفاصيل الشركة"""
        return self.select_related('company', 'service')


class InsuranceOrderManager(models.Manager):
    """Manager مخصص للطلبات"""
    
    def pending_payment(self):
        """الطلبات بانتظار الدفع"""
        return self.filter(status='pending_payment')
    
    def paid(self):
        """الطلبات المدفوعة"""
        return self.filter(status='paid')
    
    def with_full_details(self):
        """جلب الطلبات مع جميع التفاصيل"""
        return self.select_related(
            'user',
            'offer__company',
            'offer__service',
            'vehicle'
        ).prefetch_related(
            'invoice',
            'invoice__payments'
        )
