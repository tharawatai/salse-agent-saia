"""
نماذج إضافية للدفع (إن لزم الأمر)
معظم Models موجودة في insurance_core
"""
from django.db import models


# يمكن إضافة نماذج إضافية هنا إذا لزم الأمر
# مثل: PaymentGatewayConfig, RefundRequest, إلخ

class PaymentGatewayConfig(models.Model):
    """إعدادات بوابات الدفع"""
    
    GATEWAY_TYPES = [
        ('moyasar', 'Moyasar'),
        ('hyperpay', 'HyperPay'),
        ('stripe', 'Stripe'),
    ]
    
    gateway_type = models.CharField(
        max_length=20,
        choices=GATEWAY_TYPES,
        unique=True,
        verbose_name="نوع البوابة"
    )
    api_key = models.CharField(
        max_length=255,
        verbose_name="API Key"
    )
    api_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="API Secret"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
    )
    is_test_mode = models.BooleanField(
        default=True,
        verbose_name="وضع الاختبار"
    )
    
    class Meta:
        db_table = 'payment_gateway_configs'
        verbose_name = "إعدادات بوابة دفع"
        verbose_name_plural = "إعدادات بوابات الدفع"
    
    def __str__(self):
        return f"{self.get_gateway_type_display()} - {'Test' if self.is_test_mode else 'Live'}"
