"""
النماذج الأساسية لنظام التأمين
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
import uuid

from .managers import (
    ActiveManager,
    InsuranceOfferManager,
    InsuranceOrderManager
)


# ============= المستخدمين =============

class User(AbstractUser):
    """نموذج المستخدم المخصص"""
    
    user_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="رمز المستخدم"
    )
    national_id = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="رقم الهوية الوطنية",
        help_text="10 أرقام"
    )
    birth_date = models.DateField(verbose_name="تاريخ الميلاد")
    age = models.IntegerField(
        editable=False,
        verbose_name="العمر"
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="رقم الجوال"
    )
    city = models.CharField(
        max_length=100,
        verbose_name="المدينة"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"
        indexes = [
            models.Index(fields=['national_id']),
            models.Index(fields=['phone']),
            models.Index(fields=['city']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.user_code:
            self.user_code = f"USR{uuid.uuid4().hex[:8].upper()}"
        
        if self.birth_date:
            today = date.today()
            self.age = today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.user_code})"


class Vehicle(models.Model):
    """نموذج المركبة"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name="المالك"
    )
    plate_no = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="رقم اللوحة"
    )
    brand = models.CharField(
        max_length=100,
        verbose_name="الماركة"
    )
    model = models.CharField(
        max_length=100,
        verbose_name="الموديل"
    )
    model_year = models.IntegerField(
        validators=[MinValueValidator(1990), MaxValueValidator(2030)],
        verbose_name="سنة الصنع"
    )
    vehicle_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="قيمة المركبة"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicles'
        verbose_name = "مركبة"
        verbose_name_plural = "المركبات"
        indexes = [
            models.Index(fields=['plate_no']),
            models.Index(fields=['user', '-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.brand} {self.model} - {self.plate_no}"
    
    @property
    def age(self):
        """عمر المركبة بالسنوات"""
        return date.today().year - self.model_year


# ============= شركات التأمين =============

class InsuranceCompany(models.Model):
    """شركات التأمين"""
    
    company_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="رمز الشركة"
    )
    name_ar = models.CharField(
        max_length=200,
        verbose_name="الاسم بالعربية"
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name="الاسم بالإنجليزية"
    )
    logo_url = models.URLField(
        blank=True,
        verbose_name="رابط الشعار"
    )
    rating_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="التقييم"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    active = ActiveManager()
    
    class Meta:
        db_table = 'insurance_companies'
        verbose_name = "شركة تأمين"
        verbose_name_plural = "شركات التأمين"
        ordering = ['-rating_score', 'name_ar']
    
    def __str__(self):
        return self.name_ar


class InsuranceService(models.Model):
    """أنواع خدمات التأمين"""
    
    SERVICE_TYPES = [
        ('AUTO_TPL', 'تأمين ضد الغير'),
        ('AUTO_COMP', 'تأمين شامل'),
        ('AUTO_VIP', 'تأمين VIP'),
    ]
    
    service_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="رمز الخدمة"
    )
    name_ar = models.CharField(
        max_length=200,
        verbose_name="الاسم بالعربية"
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name="الاسم بالإنجليزية"
    )
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES,
        verbose_name="نوع الخدمة"
    )
    description = models.TextField(
        verbose_name="الوصف"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = models.Manager()
    active = ActiveManager()
    
    class Meta:
        db_table = 'insurance_services'
        verbose_name = "خدمة تأمين"
        verbose_name_plural = "خدمات التأمين"
    
    def __str__(self):
        return self.name_ar



class InsuranceOffer(models.Model):
    """عروض التأمين"""
    
    COVERAGE_TYPES = [
        ('tpl', 'ضد الغير'),
        ('comprehensive', 'شامل'),
        ('vip', 'VIP'),
    ]
    
    company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.CASCADE,
        related_name='offers',
        verbose_name="الشركة"
    )
    service = models.ForeignKey(
        InsuranceService,
        on_delete=models.CASCADE,
        related_name='offers',
        verbose_name="الخدمة"
    )
    offer_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="رمز العرض"
    )
    coverage_type = models.CharField(
        max_length=20,
        choices=COVERAGE_TYPES,
        verbose_name="نوع التغطية"
    )
    
    # متطلبات
    min_age = models.IntegerField(
        default=18,
        verbose_name="الحد الأدنى للعمر"
    )
    max_age = models.IntegerField(
        default=70,
        verbose_name="الحد الأقصى للعمر"
    )
    min_vehicle_year = models.IntegerField(
        default=2010,
        verbose_name="أقدم سنة مركبة"
    )
    max_vehicle_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="أقصى قيمة للمركبة"
    )
    
    # التسعير
    price_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="السعر الأساسي"
    )
    njm_discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name="خصم نجم %"
    )
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        verbose_name="ضريبة القيمة المضافة %"
    )
    
    # JSON Fields
    deductible_options = models.JSONField(
        default=list,
        verbose_name="خيارات التحمل"
    )
    included_features_json = models.JSONField(
        default=list,
        verbose_name="المزايا المضمنة"
    )
    optional_addons_json = models.JSONField(
        default=list,
        verbose_name="الإضافات الاختيارية"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = InsuranceOfferManager()
    active = ActiveManager()
    
    class Meta:
        db_table = 'insurance_offers'
        verbose_name = "عرض تأمين"
        verbose_name_plural = "عروض التأمين"
        indexes = [
            models.Index(fields=['company', 'service']),
            models.Index(fields=['coverage_type', 'is_active']),
            models.Index(fields=['price_base']),
        ]
        ordering = ['price_base']
    
    def __str__(self):
        return f"{self.company.name_ar} - {self.get_coverage_type_display()}"
    
    def calculate_final_price(self, has_njm_discount=False):
        """حساب السعر النهائي"""
        price = float(self.price_base)
        discount = 0
        
        if has_njm_discount:
            discount = price * (float(self.njm_discount_pct) / 100)
            price -= discount
        
        vat = price * (float(self.vat_rate) / 100)
        final_price = price + vat
        
        return {
            'base_price': float(self.price_base),
            'discount': discount,
            'price_after_discount': price,
            'vat': vat,
            'final_price': final_price
        }


# ============= الطلبات والفواتير =============

class InsuranceOrder(models.Model):
    """طلبات التأمين"""
    
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('awaiting_confirmation', 'بانتظار التأكيد'),
        ('pending_payment', 'بانتظار الدفع'),
        ('paid', 'مدفوع'),
        ('policy_issued', 'صدرت الوثيقة'),
        ('cancelled', 'ملغي'),
    ]
    
    order_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="رمز الطلب"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="العميل"
    )
    offer = models.ForeignKey(
        InsuranceOffer,
        on_delete=models.PROTECT,
        verbose_name="العرض"
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        verbose_name="المركبة"
    )
    
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="السعر الإجمالي"
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="الحالة"
    )
    
    has_njm_discount = models.BooleanField(
        default=False,
        verbose_name="لديه خصم نجم"
    )
    selected_deductible = models.JSONField(
        null=True,
        blank=True,
        verbose_name="التحمل المختار"
    )
    selected_addons = models.JSONField(
        default=list,
        verbose_name="الإضافات المختارة"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = InsuranceOrderManager()
    
    class Meta:
        db_table = 'insurance_orders'
        verbose_name = "طلب تأمين"
        verbose_name_plural = "طلبات التأمين"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['order_code']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = f"ORD{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order_code} - {self.user.get_full_name()}"


class Invoice(models.Model):
    """الفواتير"""
    
    STATUS_CHOICES = [
        ('pending', 'معلقة'),
        ('paid', 'مدفوعة'),
        ('expired', 'منتهية'),
        ('cancelled', 'ملغاة'),
    ]
    
    invoice_no = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="رقم الفاتورة"
    )
    order = models.OneToOneField(
        InsuranceOrder,
        on_delete=models.CASCADE,
        related_name='invoice',
        verbose_name="الطلب"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="المبلغ"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="الحالة"
    )
    expires_at = models.DateTimeField(
        verbose_name="تنتهي في"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الدفع"
    )
    
    class Meta:
        db_table = 'invoices'
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_no']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.invoice_no:
            self.invoice_no = f"INV{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.invoice_no} - {self.amount} ريال"
    
    @property
    def is_expired(self):
        """هل انتهت صلاحية الفاتورة"""
        from django.utils import timezone
        return self.expires_at < timezone.now() and self.status == 'pending'


class Payment(models.Model):
    """المدفوعات"""
    
    STATUS_CHOICES = [
        ('pending', 'معلق'),
        ('processing', 'قيد المعالجة'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('refunded', 'مسترد'),
    ]
    
    PAYMENT_METHODS = [
        ('credit_card', 'بطاقة ائتمان'),
        ('debit_card', 'بطاقة مدى'),
        ('apple_pay', 'Apple Pay'),
        ('stc_pay', 'STC Pay'),
        ('bank_transfer', 'تحويل بنكي'),
    ]
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="الفاتورة"
    )
    transaction_ref = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="رقم المعاملة"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="المبلغ"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHODS,
        verbose_name="طريقة الدفع"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="الحالة"
    )
    gateway_response = models.JSONField(
        default=dict,
        verbose_name="استجابة البوابة"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ الإتمام"
    )
    
    class Meta:
        db_table = 'payments'
        verbose_name = "دفعة"
        verbose_name_plural = "المدفوعات"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_ref']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_ref} - {self.amount} ريال"


class Policy(models.Model):
    """وثائق التأمين"""
    
    policy_no = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="رقم الوثيقة"
    )
    order = models.OneToOneField(
        InsuranceOrder,
        on_delete=models.CASCADE,
        related_name='policy',
        verbose_name="الطلب"
    )
    start_date = models.DateField(
        verbose_name="تاريخ البداية"
    )
    end_date = models.DateField(
        verbose_name="تاريخ الانتهاء"
    )
    pdf_url = models.URLField(
        verbose_name="رابط PDF"
    )
    
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإصدار"
    )
    
    class Meta:
        db_table = 'policies'
        verbose_name = "وثيقة تأمين"
        verbose_name_plural = "وثائق التأمين"
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['policy_no']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.policy_no:
            self.policy_no = f"POL{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.policy_no}"
    
    @property
    def is_active(self):
        """هل الوثيقة سارية"""
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    @property
    def days_remaining(self):
        """الأيام المتبقية"""
        if not self.is_active:
            return 0
        return (self.end_date - date.today()).days
