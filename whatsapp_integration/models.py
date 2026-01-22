"""
نماذج تكامل WhatsApp
"""
from django.db import models
from insurance_core.models import User


class WhatsAppSession(models.Model):
    """جلسات واتساب"""
    
    SESSION_STATUS = [
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
        ('blocked', 'محظور'),
    ]
    
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="رقم الجوال"
    )
    whatsapp_id = models.CharField(
        max_length=100,
        verbose_name="معرف واتساب",
        blank=True,
        default=""
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_sessions',
        verbose_name="المستخدم"
    )
    session_status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS,
        default='active',
        verbose_name="حالة الجلسة"
    )
    conversation_history = models.JSONField(
        default=list,
        blank=True,
        verbose_name="سجل المحادثة"
    )
    last_message_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر رسالة"
    )
    
    # 🆕 حقول إضافية للمحرك الاحترافي
    conversation_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="معرف المحادثة"
    )
    current_stage = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="المرحلة الحالية"
    )
    context_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="بيانات السياق"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'whatsapp_sessions'
        verbose_name = "جلسة واتساب"
        verbose_name_plural = "جلسات واتساب"
        ordering = ['-last_message_at']
    
    def __str__(self):
        return f"{self.phone_number} - {self.get_session_status_display()}"
