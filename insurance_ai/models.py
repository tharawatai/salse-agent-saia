"""
نماذج قاعدة البيانات لنظام المحادثات والجلسات
هيكلية احترافية متكاملة لحفظ كل البيانات والعمليات
"""
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


# ═══════════════════════════════════════════════════════════════
# Enums & Choices
# ═══════════════════════════════════════════════════════════════

class ConversationStatus(models.TextChoices):
    """حالات المحادثة"""
    ACTIVE = 'active', 'نشطة'
    COMPLETED = 'completed', 'مكتملة'
    ABANDONED = 'abandoned', 'متروكة'
    EXPIRED = 'expired', 'منتهية'
    CANCELLED = 'cancelled', 'ملغاة'


class ConversationStage(models.TextChoices):
    """مراحل المحادثة"""
    GREETING = 'greeting', 'الترحيب'
    SERVICE_DETAILS = 'service_details', 'تفاصيل الخدمة'
    COLLECTING_VEHICLE = 'collecting_vehicle', 'جمع بيانات السيارة'
    CONFIRMING_VEHICLE = 'confirming_vehicle', 'تأكيد بيانات السيارة'
    SHOWING_OFFERS = 'showing_offers', 'عرض العروض'
    OFFER_DETAILS = 'offer_details', 'تفاصيل العرض'
    COLLECTING_PROFILE = 'collecting_profile', 'جمع بيانات العميل'
    CONFIRMING_PROFILE = 'confirming_profile', 'تأكيد بيانات العميل'
    ORDER_SUMMARY = 'order_summary', 'ملخص الطلب'
    CONFIRMATION = 'confirmation', 'التأكيد النهائي'
    PAYMENT_PENDING = 'payment_pending', 'انتظار الدفع'
    COMPLETED = 'completed', 'مكتمل'


class MessageRole(models.TextChoices):
    """أدوار الرسائل"""
    USER = 'user', 'المستخدم'
    ASSISTANT = 'assistant', 'المساعد'
    SYSTEM = 'system', 'النظام'


class MessageType(models.TextChoices):
    """أنواع الرسائل"""
    TEXT = 'text', 'نص'
    IMAGE = 'image', 'صورة'
    DOCUMENT = 'document', 'مستند'
    LOCATION = 'location', 'موقع'
    BUTTON_RESPONSE = 'button_response', 'رد زر'
    LIST_RESPONSE = 'list_response', 'رد قائمة'


class ChannelType(models.TextChoices):
    """قنوات التواصل"""
    WHATSAPP = 'whatsapp', 'واتساب'
    WEB_CHAT = 'web_chat', 'محادثة الويب'
    API = 'api', 'API'
    MOBILE_APP = 'mobile_app', 'تطبيق الجوال'


# ═══════════════════════════════════════════════════════════════
# Conversation Session - جلسة المحادثة الرئيسية
# ═══════════════════════════════════════════════════════════════

class ConversationSession(models.Model):
    """
    جلسة المحادثة الرئيسية
    تحفظ كل بيانات الجلسة من البداية للنهاية
    """
    
    # المعرفات
    session_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="معرف الجلسة"
    )
    
    # معلومات المستخدم
    user_identifier = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="معرف المستخدم",
        help_text="رقم الهاتف أو معرف فريد"
    )
    user = models.ForeignKey(
        'insurance_core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_sessions',
        verbose_name="المستخدم المسجل"
    )
    
    # القناة
    channel = models.CharField(
        max_length=20,
        choices=ChannelType.choices,
        default=ChannelType.WHATSAPP,
        verbose_name="قناة التواصل"
    )
    
    # الحالة والمرحلة
    status = models.CharField(
        max_length=20,
        choices=ConversationStatus.choices,
        default=ConversationStatus.ACTIVE,
        db_index=True,
        verbose_name="حالة الجلسة"
    )
    current_stage = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        default=ConversationStage.GREETING,
        verbose_name="المرحلة الحالية"
    )
    previous_stage = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        null=True,
        blank=True,
        verbose_name="المرحلة السابقة"
    )
    
    # إحصائيات
    message_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد الرسائل"
    )
    stage_transitions_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد الانتقالات"
    )
    
    # الروابط بالنتائج
    order = models.ForeignKey(
        'insurance_core.InsuranceOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_sessions',
        verbose_name="الطلب الناتج"
    )
    
    # التوقيتات
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    last_activity_at = models.DateTimeField(auto_now=True, verbose_name="آخر نشاط")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاكتمال")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الانتهاء")
    
    # بيانات إضافية
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="بيانات إضافية"
    )
    
    class Meta:
        db_table = 'conversation_sessions'
        verbose_name = "جلسة محادثة"
        verbose_name_plural = "جلسات المحادثات"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user_identifier']),
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['-last_activity_at']),
            models.Index(fields=['channel', 'status']),
        ]
    
    def __str__(self):
        return f"Session {str(self.session_id)[:8]} - {self.user_identifier}"
    
    def mark_completed(self):
        """تحديد الجلسة كمكتملة"""
        self.status = ConversationStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    def mark_abandoned(self):
        """تحديد الجلسة كمتروكة"""
        self.status = ConversationStatus.ABANDONED
        self.save(update_fields=['status', 'updated_at'])
    
    def update_stage(self, new_stage: str):
        """تحديث المرحلة"""
        if self.current_stage != new_stage:
            self.previous_stage = self.current_stage
            self.current_stage = new_stage
            self.stage_transitions_count += 1
            self.save(update_fields=['current_stage', 'previous_stage', 'stage_transitions_count', 'updated_at'])


# ═══════════════════════════════════════════════════════════════
# Vehicle Data - بيانات السيارة المجمعة
# ═══════════════════════════════════════════════════════════════

class SessionVehicleData(models.Model):
    """
    بيانات السيارة المجمعة خلال الجلسة
    تحفظ حتى لو لم تكتمل العملية
    """
    
    session = models.OneToOneField(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='vehicle_data',
        verbose_name="الجلسة"
    )
    
    # البيانات الأساسية
    brand = models.CharField(max_length=100, null=True, blank=True, verbose_name="الماركة")
    model = models.CharField(max_length=100, null=True, blank=True, verbose_name="الموديل")
    year = models.PositiveIntegerField(null=True, blank=True, verbose_name="سنة الصنع")
    value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="القيمة")
    plate_no = models.CharField(max_length=20, null=True, blank=True, verbose_name="رقم اللوحة")
    
    # نوع التأمين
    service_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="نوع التأمين",
        help_text="comprehensive أو tpl"
    )
    
    # حالة التأكيد
    is_confirmed = models.BooleanField(default=False, verbose_name="تم التأكيد")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ التأكيد")
    
    # حالة الاكتمال
    is_complete = models.BooleanField(default=False, verbose_name="البيانات مكتملة")
    
    # التوقيتات
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # المركبة المنشأة (إن وجدت)
    vehicle = models.ForeignKey(
        'insurance_core.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_data',
        verbose_name="المركبة المسجلة"
    )
    
    class Meta:
        db_table = 'session_vehicle_data'
        verbose_name = "بيانات سيارة الجلسة"
        verbose_name_plural = "بيانات سيارات الجلسات"
    
    def __str__(self):
        return f"{self.brand or '?'} {self.model or '?'} - {self.plate_no or '?'}"
    
    def check_completeness(self):
        """التحقق من اكتمال البيانات"""
        self.is_complete = all([self.brand, self.model, self.year, self.value, self.plate_no])
        self.save(update_fields=['is_complete', 'updated_at'])
        return self.is_complete
    
    def save(self, *args, **kwargs):
        # تحديث حالة الاكتمال تلقائياً
        self.is_complete = all([self.brand, self.model, self.year, self.value, self.plate_no])
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════
# Profile Data - بيانات العميل المجمعة
# ═══════════════════════════════════════════════════════════════

class SessionProfileData(models.Model):
    """
    بيانات العميل المجمعة خلال الجلسة
    تحفظ حتى لو لم تكتمل العملية
    """
    
    session = models.OneToOneField(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='profile_data',
        verbose_name="الجلسة"
    )
    
    # البيانات الأساسية
    national_id = models.CharField(max_length=10, null=True, blank=True, verbose_name="رقم الهوية")
    birth_date = models.DateField(null=True, blank=True, verbose_name="تاريخ الميلاد")
    full_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="الاسم الكامل")
    phone = models.CharField(max_length=15, null=True, blank=True, verbose_name="رقم الجوال")
    email = models.EmailField(null=True, blank=True, verbose_name="البريد الإلكتروني")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="المدينة")
    
    # حالة التأكيد
    is_confirmed = models.BooleanField(default=False, verbose_name="تم التأكيد")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ التأكيد")
    
    # حالة الاكتمال
    is_complete = models.BooleanField(default=False, verbose_name="البيانات مكتملة")
    
    # التوقيتات
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'session_profile_data'
        verbose_name = "بيانات عميل الجلسة"
        verbose_name_plural = "بيانات عملاء الجلسات"
    
    def __str__(self):
        return f"{self.full_name or self.national_id or 'Unknown'}"
    
    def save(self, *args, **kwargs):
        # تحديث حالة الاكتمال تلقائياً
        self.is_complete = all([self.national_id, self.birth_date])
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════
# Offers Data - العروض المعروضة والمختارة
# ═══════════════════════════════════════════════════════════════

class SessionOffersData(models.Model):
    """
    العروض المعروضة خلال الجلسة
    """
    
    session = models.OneToOneField(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='offers_data',
        verbose_name="الجلسة"
    )
    
    # العروض المعروضة (JSON array)
    shown_offers = models.JSONField(
        default=list,
        verbose_name="العروض المعروضة"
    )
    shown_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ العرض")
    
    # العرض المختار
    selected_offer = models.ForeignKey(
        'insurance_core.InsuranceOffer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_selections',
        verbose_name="العرض المختار"
    )
    selected_offer_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="بيانات العرض المختار"
    )
    selected_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاختيار")
    
    # تأكيد العرض
    is_confirmed = models.BooleanField(default=False, verbose_name="تم تأكيد العرض")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ التأكيد")
    
    # التوقيتات
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'session_offers_data'
        verbose_name = "عروض الجلسة"
        verbose_name_plural = "عروض الجلسات"
    
    def __str__(self):
        count = len(self.shown_offers) if self.shown_offers else 0
        return f"{count} offers - Selected: {self.selected_offer_id or 'None'}"


# ═══════════════════════════════════════════════════════════════
# Messages - سجل الرسائل
# ═══════════════════════════════════════════════════════════════

class ConversationMessage(models.Model):
    """
    سجل رسائل المحادثة
    """
    
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="الجلسة"
    )
    
    # معرف الرسالة
    message_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name="معرف الرسالة"
    )
    
    # الدور والنوع
    role = models.CharField(
        max_length=20,
        choices=MessageRole.choices,
        verbose_name="الدور"
    )
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        verbose_name="نوع الرسالة"
    )
    
    # المحتوى
    content = models.TextField(verbose_name="المحتوى")
    
    # المرحلة عند إرسال الرسالة
    stage_at_message = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        verbose_name="المرحلة"
    )
    
    # بيانات مستخرجة من الرسالة (إن وجدت)
    extracted_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="البيانات المستخرجة"
    )
    
    # تحليل AI
    ai_analysis = models.JSONField(
        null=True,
        blank=True,
        verbose_name="تحليل AI"
    )
    
    # التوقيت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    
    # بيانات إضافية
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="بيانات إضافية"
    )
    
    class Meta:
        db_table = 'conversation_messages'
        verbose_name = "رسالة محادثة"
        verbose_name_plural = "رسائل المحادثات"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['role']),
            models.Index(fields=['stage_at_message']),
        ]
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


# ═══════════════════════════════════════════════════════════════
# Stage Transitions - سجل الانتقالات بين المراحل
# ═══════════════════════════════════════════════════════════════

class StageTransition(models.Model):
    """
    سجل الانتقالات بين المراحل
    يتتبع كل انتقال مع السبب والبيانات
    """
    
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='stage_transitions',
        verbose_name="الجلسة"
    )
    
    # المراحل
    from_stage = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        verbose_name="من مرحلة"
    )
    to_stage = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        verbose_name="إلى مرحلة"
    )
    
    # سبب الانتقال
    trigger_type = models.CharField(
        max_length=50,
        verbose_name="نوع المحفز",
        help_text="user_input, ai_decision, system, timeout"
    )
    trigger_message = models.ForeignKey(
        ConversationMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_transitions',
        verbose_name="الرسالة المحفزة"
    )
    
    # هل نجح الانتقال
    is_successful = models.BooleanField(default=True, verbose_name="ناجح")
    failure_reason = models.TextField(null=True, blank=True, verbose_name="سبب الفشل")
    
    # البيانات عند الانتقال
    data_snapshot = models.JSONField(
        default=dict,
        verbose_name="لقطة البيانات"
    )
    
    # التوقيت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانتقال")
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="المدة بالثواني",
        help_text="الوقت المستغرق في المرحلة السابقة"
    )
    
    class Meta:
        db_table = 'stage_transitions'
        verbose_name = "انتقال مرحلة"
        verbose_name_plural = "انتقالات المراحل"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['from_stage', 'to_stage']),
        ]
    
    def __str__(self):
        return f"{self.from_stage} → {self.to_stage}"


# ═══════════════════════════════════════════════════════════════
# Session Results - نتائج الجلسة
# ═══════════════════════════════════════════════════════════════

class SessionResult(models.Model):
    """
    نتائج الجلسة النهائية
    تربط الجلسة بالطلب والفاتورة والوثيقة
    """
    
    session = models.OneToOneField(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name="الجلسة"
    )
    
    # النتائج
    order = models.ForeignKey(
        'insurance_core.InsuranceOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_results',
        verbose_name="الطلب"
    )
    invoice = models.ForeignKey(
        'insurance_core.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_results',
        verbose_name="الفاتورة"
    )
    policy = models.ForeignKey(
        'insurance_core.Policy',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_results',
        verbose_name="الوثيقة"
    )
    
    # حالة النتيجة
    is_order_created = models.BooleanField(default=False, verbose_name="تم إنشاء الطلب")
    is_invoice_created = models.BooleanField(default=False, verbose_name="تم إنشاء الفاتورة")
    is_payment_completed = models.BooleanField(default=False, verbose_name="تم الدفع")
    is_policy_issued = models.BooleanField(default=False, verbose_name="تم إصدار الوثيقة")
    
    # التوقيتات
    order_created_at = models.DateTimeField(null=True, blank=True)
    invoice_created_at = models.DateTimeField(null=True, blank=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    policy_issued_at = models.DateTimeField(null=True, blank=True)
    
    # ملخص
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="المبلغ الإجمالي"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'session_results'
        verbose_name = "نتيجة جلسة"
        verbose_name_plural = "نتائج الجلسات"
    
    def __str__(self):
        status = []
        if self.is_order_created: status.append("Order")
        if self.is_invoice_created: status.append("Invoice")
        if self.is_payment_completed: status.append("Paid")
        if self.is_policy_issued: status.append("Policy")
        return f"Result: {' → '.join(status) or 'Pending'}"


# ═══════════════════════════════════════════════════════════════
# Analytics - إحصائيات وتحليلات
# ═══════════════════════════════════════════════════════════════

class ModificationEventType(models.TextChoices):
    """أنواع أحداث التعديل"""
    CANCEL = 'cancel', 'إلغاء كامل'
    EDIT_VEHICLE = 'edit_vehicle', 'تعديل بيانات السيارة'
    EDIT_PROFILE = 'edit_profile', 'تعديل البيانات الشخصية'
    CHANGE_OFFER = 'change_offer', 'تغيير العرض'
    GO_BACK = 'go_back', 'رجوع للخطوة السابقة'
    RESTART = 'restart', 'إعادة البدء'


class SessionModificationEvent(models.Model):
    """
    سجل أحداث التعديل والرجوع والإلغاء
    يتتبع كل تعديل يقوم به المستخدم مع البيانات قبل وبعد
    """
    
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='modification_events',
        verbose_name="الجلسة"
    )
    
    # نوع الحدث
    event_type = models.CharField(
        max_length=20,
        choices=ModificationEventType.choices,
        verbose_name="نوع الحدث"
    )
    
    # المرحلة عند الحدث
    stage_at_event = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        verbose_name="المرحلة عند الحدث"
    )
    target_stage = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        verbose_name="المرحلة المستهدفة"
    )
    
    # البيانات قبل التعديل (snapshot)
    data_before = models.JSONField(
        default=dict,
        verbose_name="البيانات قبل التعديل"
    )
    
    # البيانات بعد التعديل (ما تم مسحه/تغييره)
    data_after = models.JSONField(
        default=dict,
        verbose_name="البيانات بعد التعديل"
    )
    
    # سبب التعديل (من AI أو المستخدم)
    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="سبب التعديل"
    )
    
    # رسالة المستخدم التي أدت للتعديل
    trigger_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="رسالة المستخدم"
    )
    
    # رد النظام
    system_response = models.TextField(
        null=True,
        blank=True,
        verbose_name="رد النظام"
    )
    
    # هل نجح التعديل
    is_successful = models.BooleanField(
        default=True,
        verbose_name="نجح التعديل"
    )
    
    # التوقيت
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الحدث"
    )
    
    # بيانات إضافية
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="بيانات إضافية"
    )
    
    class Meta:
        db_table = 'session_modification_events'
        verbose_name = "حدث تعديل"
        verbose_name_plural = "أحداث التعديل"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['stage_at_event']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.stage_at_event} → {self.target_stage}"


class SessionAnalytics(models.Model):
    """
    إحصائيات وتحليلات الجلسة
    """
    
    session = models.OneToOneField(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name="الجلسة"
    )
    
    # مدة الجلسة
    total_duration_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="المدة الإجمالية (ثواني)"
    )
    active_duration_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="مدة النشاط (ثواني)"
    )
    
    # إحصائيات الرسائل
    user_messages_count = models.PositiveIntegerField(default=0, verbose_name="رسائل المستخدم")
    assistant_messages_count = models.PositiveIntegerField(default=0, verbose_name="رسائل المساعد")
    avg_response_time_seconds = models.FloatField(null=True, blank=True, verbose_name="متوسط وقت الرد")
    
    # إحصائيات المراحل
    stages_visited = models.JSONField(default=list, verbose_name="المراحل المزارة")
    time_per_stage = models.JSONField(default=dict, verbose_name="الوقت لكل مرحلة")
    
    # نقاط التوقف
    drop_off_stage = models.CharField(
        max_length=30,
        choices=ConversationStage.choices,
        null=True,
        blank=True,
        verbose_name="مرحلة التوقف"
    )
    
    # تقييم الجودة
    ai_confidence_avg = models.FloatField(null=True, blank=True, verbose_name="متوسط ثقة AI")
    extraction_accuracy = models.FloatField(null=True, blank=True, verbose_name="دقة الاستخراج")
    
    # إحصائيات التعديلات
    total_modifications = models.PositiveIntegerField(
        default=0,
        verbose_name="إجمالي التعديلات"
    )
    cancel_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد الإلغاءات"
    )
    edit_vehicle_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد تعديلات السيارة"
    )
    edit_profile_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد تعديلات البيانات الشخصية"
    )
    change_offer_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد تغييرات العرض"
    )
    go_back_count = models.PositiveIntegerField(
        default=0,
        verbose_name="عدد الرجوع"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'session_analytics'
        verbose_name = "تحليلات جلسة"
        verbose_name_plural = "تحليلات الجلسات"
    
    def __str__(self):
        return f"Analytics for {self.session.session_id}"
    
    def calculate_duration(self):
        """حساب مدة الجلسة"""
        if self.session.completed_at:
            delta = self.session.completed_at - self.session.created_at
            self.total_duration_seconds = int(delta.total_seconds())
            self.save(update_fields=['total_duration_seconds', 'updated_at'])


# ═══════════════════════════════════════════════════════════════
# Thread & Message - متوافق مع django_ai_assistant
# ═══════════════════════════════════════════════════════════════

class Thread(models.Model):
    """
    Thread model - متوافق مع django_ai_assistant
    محادثة بين المستخدم والمساعد
    """
    
    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="اسم المحادثة"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='ai_threads',
        null=True,
        blank=True,
        verbose_name="المنشئ"
    )
    
    assistant_id = models.CharField(
        max_length=255,
        blank=True,
        default='insurance-assistant',
        verbose_name="معرف المساعد"
    )
    
    # ربط بالجلسة القديمة (اختياري)
    conversation_session = models.ForeignKey(
        ConversationSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='threads',
        verbose_name="جلسة المحادثة"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    class Meta:
        db_table = 'ai_threads'
        verbose_name = "محادثة AI"
        verbose_name_plural = "محادثات AI"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['assistant_id']),
        ]
    
    def __str__(self):
        return self.name or f"Thread {self.id}"
    
    def __repr__(self):
        return f"<Thread {self.name}>"
    
    def get_messages(self, include_extra_messages: bool = False):
        """
        الحصول على رسائل المحادثة
        متوافق مع django_ai_assistant
        """
        messages = self.ai_messages.order_by('created_at')
        
        if not include_extra_messages:
            # فقط رسائل human و ai
            messages = messages.filter(message_type__in=['human', 'ai'])
        
        return list(messages)


class Message(models.Model):
    """
    Message model - متوافق مع django_ai_assistant
    رسالة في المحادثة
    """
    
    MESSAGE_TYPES = [
        ('human', 'رسالة المستخدم'),
        ('ai', 'رسالة المساعد'),
        ('system', 'رسالة النظام'),
        ('tool', 'استدعاء أداة'),
    ]
    
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name='ai_messages',
        verbose_name="المحادثة"
    )
    
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='human',
        verbose_name="نوع الرسالة"
    )
    
    content = models.TextField(
        verbose_name="المحتوى"
    )
    
    # بيانات إضافية (stage, data, etc.)
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="بيانات إضافية"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    class Meta:
        db_table = 'ai_messages'
        verbose_name = "رسالة AI"
        verbose_name_plural = "رسائل AI"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['message_type']),
        ]
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."
    
    def __repr__(self):
        return f"<Message {self.id} at {self.thread_id}>"
