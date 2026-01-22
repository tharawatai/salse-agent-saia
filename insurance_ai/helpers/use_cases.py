"""
Use Cases - Business Logic Layer
متوافق مع django_ai_assistant/helpers/use_cases.py
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from django.db import transaction
from asgiref.sync import sync_to_async

from ..assistants.base import AIAssistant
from ..models import Thread, Message

logger = logging.getLogger(__name__)


# ==================== Assistants ====================

def get_assistants_info(user=None, request=None) -> List[Dict]:
    """
    الحصول على قائمة المساعدين المسجلين
    
    Returns:
        List of assistant info dicts
    """
    registry = AIAssistant.get_cls_registry()
    
    assistants = []
    for assistant_id, assistant_cls in registry.items():
        assistants.append({
            'id': assistant_cls.id,
            'name': assistant_cls.name,
            'model': getattr(assistant_cls, 'model', 'gemini-2.0-flash'),
        })
    
    return assistants


def get_single_assistant_info(
    assistant_id: str,
    user=None,
    request=None
) -> Optional[Dict]:
    """
    الحصول على معلومات مساعد محدد
    
    Args:
        assistant_id: معرف المساعد
        
    Returns:
        Assistant info dict or None
    """
    try:
        assistant_cls = AIAssistant.get_cls(assistant_id)
        return {
            'id': assistant_cls.id,
            'name': assistant_cls.name,
            'model': getattr(assistant_cls, 'model', 'gemini-2.0-flash'),
        }
    except KeyError:
        return None


# ==================== Threads ====================

def get_threads(
    user=None,
    assistant_id: Optional[str] = None
) -> List[Thread]:
    """
    الحصول على قائمة المحادثات
    
    Args:
        user: المستخدم (اختياري)
        assistant_id: فلترة بمعرف المساعد
        
    Returns:
        List of Thread objects
    """
    queryset = Thread.objects.all()
    
    if user and user.is_authenticated:
        queryset = queryset.filter(created_by=user)
    
    if assistant_id:
        queryset = queryset.filter(assistant_id=assistant_id)
    
    return list(queryset.order_by('-created_at'))


def get_single_thread(
    thread_id: int,
    user=None,
    request=None
) -> Optional[Thread]:
    """
    الحصول على محادثة محددة
    """
    try:
        thread = Thread.objects.get(id=thread_id)
        # يمكن إضافة permission check هنا
        return thread
    except Thread.DoesNotExist:
        return None


def create_thread(
    name: str = "",
    assistant_id: str = "insurance-assistant",
    user=None,
    request=None
) -> Thread:
    """
    إنشاء محادثة جديدة
    
    Args:
        name: اسم المحادثة
        assistant_id: معرف المساعد
        user: المستخدم
        
    Returns:
        Thread object
    """
    thread = Thread.objects.create(
        name=name or f"محادثة {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        assistant_id=assistant_id,
        created_by=user if user and user.is_authenticated else None
    )
    
    logger.info(f"📝 Created thread: {thread.id} for assistant: {assistant_id}")
    return thread


def update_thread(
    thread: Thread,
    name: str,
    user=None,
    request=None
) -> Thread:
    """
    تحديث محادثة
    """
    thread.name = name
    thread.save()
    return thread


def delete_thread(
    thread: Thread,
    user=None,
    request=None
) -> None:
    """
    حذف محادثة
    """
    thread_id = thread.id
    thread.delete()
    logger.info(f"🗑️ Deleted thread: {thread_id}")


# ==================== Messages ====================

def get_thread_messages(
    thread: Thread,
    user=None,
    request=None
) -> List[Dict]:
    """
    الحصول على رسائل المحادثة
    
    Returns:
        List of message dicts
    """
    messages = Message.objects.filter(thread=thread).order_by('created_at')
    
    return [
        {
            'id': m.id,
            'type': m.message_type,
            'content': m.content,
            'created_at': m.created_at,
            'extra_data': m.extra_data,
        }
        for m in messages
    ]


async def create_message(
    assistant_id: str,
    thread: Thread,
    content: str,
    user=None,
    phone: str = None,
    request=None
) -> Dict:
    """
    إنشاء رسالة جديدة ومعالجتها بالمساعد
    
    Args:
        assistant_id: معرف المساعد
        thread: المحادثة
        content: محتوى الرسالة
        user: المستخدم
        phone: رقم الهاتف
        
    Returns:
        Response dict
    """
    # حفظ رسالة المستخدم
    @sync_to_async
    def save_user_message():
        return Message.objects.create(
            thread=thread,
            message_type='human',
            content=content
        )
    
    user_message = await save_user_message()
    logger.info(f"💬 User message saved: {user_message.id}")
    
    try:
        # الحصول على المساعد
        assistant_cls = AIAssistant.get_cls(assistant_id)
        assistant = assistant_cls(user=user, request=request)
        
        # معالجة الرسالة
        result = await assistant.run(
            message=content,
            thread_id=thread.id,
            phone=phone
        )
        
        # حفظ رد المساعد
        @sync_to_async
        def save_ai_message():
            return Message.objects.create(
                thread=thread,
                message_type='ai',
                content=result.get('output', ''),
                extra_data={
                    'stage': result.get('stage'),
                    'data': result.get('data'),
                    'has_invoice': result.get('has_invoice', False),
                    'invoice_url': result.get('invoice_url'),
                    'has_policy': result.get('has_policy', False),
                    'policy_url': result.get('policy_url'),
                }
            )
        
        ai_message = await save_ai_message()
        logger.info(f"🤖 AI message saved: {ai_message.id}")
        
        return {
            'success': result.get('success', True),
            'response': result.get('output', ''),
            'stage': result.get('stage'),
            'data': result.get('data'),
            'has_invoice': result.get('has_invoice', False),
            'invoice_url': result.get('invoice_url'),
            'has_policy': result.get('has_policy', False),
            'policy_url': result.get('policy_url'),
        }
        
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        
        # حفظ رسالة خطأ
        @sync_to_async
        def save_error_message():
            return Message.objects.create(
                thread=thread,
                message_type='ai',
                content='عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.',
                extra_data={'error': str(e)}
            )
        
        await save_error_message()
        
        return {
            'success': False,
            'response': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.',
            'error': str(e)
        }


def delete_message(
    message: Message,
    user=None,
    request=None
) -> None:
    """
    حذف رسالة
    """
    message_id = message.id
    message.delete()
    logger.info(f"🗑️ Deleted message: {message_id}")


# ==================== Quick Chat ====================

async def quick_chat(
    assistant_id: str,
    content: str,
    phone: str = None,
    user=None,
    request=None
) -> Dict:
    """
    محادثة سريعة بدون thread
    للتوافق مع الـ API القديم
    """
    try:
        # الحصول على المساعد
        assistant_cls = AIAssistant.get_cls(assistant_id)
        assistant = assistant_cls(user=user, request=request)
        
        # استخدام phone كـ thread_id
        thread_id = f"quick_{phone}" if phone else None
        
        # معالجة الرسالة
        result = await assistant.run(
            message=content,
            thread_id=thread_id,
            phone=phone
        )
        
        return {
            'success': result.get('success', True),
            'response': result.get('output', ''),
            'stage': result.get('stage'),
            'data': result.get('data'),
            'has_invoice': result.get('has_invoice', False),
            'invoice_url': result.get('invoice_url'),
            'has_policy': result.get('has_policy', False),
            'policy_url': result.get('policy_url'),
        }
        
    except KeyError:
        return {
            'success': False,
            'response': f'المساعد "{assistant_id}" غير موجود',
        }
    except Exception as e:
        logger.exception(f"Error in quick_chat: {e}")
        return {
            'success': False,
            'response': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.',
            'error': str(e)
        }
