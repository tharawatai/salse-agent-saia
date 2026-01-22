"""
WhatsApp Webhook Handler
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import logging
import requests

from .models import WhatsAppSession
from insurance_core.models import User

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    Webhook لاستقبال رسائل WhatsApp
    """
    if request.method == "GET":
        # التحقق من Webhook (Meta verification)
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        
        VERIFY_TOKEN = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', 'your_verify_token')
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse("Verification failed", status=403)
    
    # معالجة الرسائل الواردة
    try:
        body = json.loads(request.body)
        
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return JsonResponse({"status": "no_messages"})
        
        message = messages[0]
        phone_number = message.get("from")
        message_text = message.get("text", {}).get("body", "")
        whatsapp_id = message.get("id")
        
        # معالجة الرسالة
        response_text = process_whatsapp_message(
            phone_number=phone_number,
            message_text=message_text,
            whatsapp_id=whatsapp_id
        )
        
        # إرسال الرد
        send_whatsapp_message(phone_number, response_text)
        
        return JsonResponse({"status": "success"})
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def process_whatsapp_message(phone_number: str, message_text: str, whatsapp_id: str) -> str:
    """
    معالجة رسالة WhatsApp باستخدام AI Assistant
    """
    # الحصول على أو إنشاء جلسة WhatsApp
    session, _ = WhatsAppSession.objects.get_or_create(
        phone_number=phone_number,
        defaults={"whatsapp_id": whatsapp_id}
    )
    
    # محاولة ربط المستخدم
    user = None
    if session.user:
        user = session.user
    else:
        # محاولة العثور على المستخدم برقم الجوال
        try:
            user = User.objects.get(phone=phone_number)
            session.user = user
            session.save()
        except User.DoesNotExist:
            pass
    
    # الحصول على أو إنشاء Thread
    from django_ai_assistant.models import Thread
    
    thread, created = Thread.objects.get_or_create(
        name=f"WhatsApp: {phone_number}",
        created_by=user,
        defaults={
            "assistant_id": "insurance_main_assistant"
        }
    )
    
    # تشغيل المساعد
    from insurance_ai.ai_assistants import InsuranceMainAssistant
    
    assistant = InsuranceMainAssistant(user=user, request=None)
    
    try:
        # تشغيل المساعد مع الرسالة
        response = assistant.run(
            message=message_text,
            thread_id=thread.id
        )
        return response
    except Exception as e:
        logger.error(f"Error running assistant: {str(e)}")
        return "عذراً، حدث خطأ في معالجة رسالتك. يرجى المحاولة مرة أخرى."


def send_whatsapp_message(phone_number: str, message: str):
    """
    إرسال رسالة عبر WhatsApp Business API
    """
    try:
        phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        
        if not phone_number_id or not access_token:
            logger.warning("WhatsApp credentials not configured")
            return None
        
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to send WhatsApp message: {response.text}")
        else:
            logger.info(f"WhatsApp message sent successfully to {phone_number}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        return None


def send_whatsapp_document(phone_number: str, document_url: str, filename: str, caption: str = None):
    """
    إرسال ملف PDF عبر WhatsApp Business API
    
    Args:
        phone_number: رقم الهاتف
        document_url: رابط الملف (يجب أن يكون رابط عام قابل للوصول)
        filename: اسم الملف
        caption: وصف الملف (اختياري)
    """
    try:
        phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        
        if not phone_number_id or not access_token:
            logger.warning("WhatsApp credentials not configured")
            return None
        
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }
        
        if caption:
            payload["document"]["caption"] = caption
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to send WhatsApp document: {response.text}")
        else:
            logger.info(f"WhatsApp document sent successfully to {phone_number}: {filename}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp document: {str(e)}")
        return None


def upload_media_to_whatsapp(file_path: str, mime_type: str = "application/pdf") -> str:
    """
    رفع ملف إلى WhatsApp Media API والحصول على media_id
    
    Args:
        file_path: مسار الملف المحلي
        mime_type: نوع الملف
    
    Returns:
        media_id أو None
    """
    try:
        phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        
        if not phone_number_id or not access_token:
            logger.warning("WhatsApp credentials not configured")
            return None
        
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/media"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.split('/')[-1], f, mime_type),
            }
            data = {
                'messaging_product': 'whatsapp',
                'type': mime_type,
            }
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            media_id = response.json().get('id')
            logger.info(f"Media uploaded successfully: {media_id}")
            return media_id
        else:
            logger.error(f"Failed to upload media: {response.text}")
            return None
        
    except Exception as e:
        logger.error(f"Error uploading media: {str(e)}")
        return None


def send_whatsapp_document_by_id(phone_number: str, media_id: str, filename: str, caption: str = None):
    """
    إرسال ملف عبر WhatsApp باستخدام media_id
    
    Args:
        phone_number: رقم الهاتف
        media_id: معرف الملف المرفوع
        filename: اسم الملف
        caption: وصف الملف (اختياري)
    """
    try:
        phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
        access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
        
        if not phone_number_id or not access_token:
            logger.warning("WhatsApp credentials not configured")
            return None
        
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "document",
            "document": {
                "id": media_id,
                "filename": filename
            }
        }
        
        if caption:
            payload["document"]["caption"] = caption
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to send WhatsApp document: {response.text}")
        else:
            logger.info(f"WhatsApp document sent successfully to {phone_number}: {filename}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp document: {str(e)}")
        return None


async def send_invoice_pdf_to_whatsapp(phone_number: str, pdf_path: str, invoice_no: str):
    """
    إرسال فاتورة PDF عبر واتساب
    
    Args:
        phone_number: رقم الهاتف
        pdf_path: مسار ملف PDF
        invoice_no: رقم الفاتورة
    """
    import asyncio
    from pathlib import Path
    
    try:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return False
        
        # رفع الملف للحصول على media_id
        media_id = await asyncio.to_thread(
            upload_media_to_whatsapp, 
            str(pdf_path), 
            "application/pdf"
        )
        
        if media_id:
            # إرسال الملف
            filename = f"فاتورة_{invoice_no}.pdf"
            caption = f"📄 فاتورة رقم: {invoice_no}\nشركة SAIA للتأمين"
            
            await asyncio.to_thread(
                send_whatsapp_document_by_id,
                phone_number,
                media_id,
                filename,
                caption
            )
            return True
        else:
            logger.warning("Could not upload PDF, falling back to URL")
            return False
            
    except Exception as e:
        logger.error(f"Error sending invoice PDF: {e}")
        return False
