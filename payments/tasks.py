"""
Celery Tasks للمهام الخلفية
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from insurance_core.models import Invoice, Payment
import logging

logger = logging.getLogger(__name__)


@shared_task
def expire_old_invoices():
    """
    تحديث حالة الفواتير المنتهية
    يتم تشغيلها كل ساعة
    """
    expired_invoices = Invoice.objects.filter(
        status='pending',
        expires_at__lt=timezone.now()
    )
    
    count = expired_invoices.count()
    
    # تحديث حالة الفواتير
    expired_invoices.update(status='expired')
    
    # تحديث حالة الطلبات المرتبطة
    for invoice in expired_invoices:
        if invoice.order.status == 'pending_payment':
            invoice.order.status = 'cancelled'
            invoice.order.save()
    
    logger.info(f"Expired {count} invoices")
    return f"Expired {count} invoices"


@shared_task
def send_payment_reminders():
    """
    إرسال تذكيرات الدفع للفواتير المعلقة
    يتم تشغيلها يومياً الساعة 10 صباحاً
    """
    # الفواتير التي ستنتهي خلال 6 ساعات
    soon_to_expire = Invoice.objects.filter(
        status='pending',
        expires_at__lt=timezone.now() + timedelta(hours=6),
        expires_at__gt=timezone.now()
    ).select_related('order__user')
    
    count = 0
    for invoice in soon_to_expire:
        try:
            send_reminder_message(
                phone=invoice.order.user.phone,
                invoice_no=invoice.invoice_no,
                amount=invoice.amount,
                expires_at=invoice.expires_at
            )
            count += 1
        except Exception as e:
            logger.error(f"Failed to send reminder for {invoice.invoice_no}: {str(e)}")
    
    logger.info(f"Sent {count} payment reminders")
    return f"Sent {count} reminders"


def send_reminder_message(phone, invoice_no, amount, expires_at):
    """إرسال رسالة تذكير عبر WhatsApp"""
    # TODO: تكامل مع WhatsApp API
    message = f"""
🔔 تذكير: فاتورة معلقة

رقم الفاتورة: {invoice_no}
المبلغ: {amount} ريال
تنتهي في: {expires_at.strftime('%Y-%m-%d %H:%M')}

يرجى إتمام الدفع قبل انتهاء الصلاحية.
    """
    
    logger.info(f"Reminder sent to {phone}: {message.strip()}")
    # هنا يمكن إضافة كود إرسال WhatsApp الفعلي


@shared_task
def generate_policy_pdf(policy_id: int):
    """
    توليد PDF لوثيقة التأمين
    """
    from insurance_core.models import Policy
    
    try:
        policy = Policy.objects.select_related(
            'order__user',
            'order__vehicle',
            'order__offer__company'
        ).get(id=policy_id)
        
        # TODO: تكامل مع مولد PDF
        pdf_path = f"/media/policies/{policy.policy_no}.pdf"
        
        # تحديث URL
        policy.pdf_url = pdf_path
        policy.save()
        
        logger.info(f"Generated PDF for policy {policy.policy_no}")
        return f"Generated PDF for policy {policy.policy_no}"
        
    except Policy.DoesNotExist:
        logger.error(f"Policy {policy_id} not found")
        return f"Policy {policy_id} not found"
