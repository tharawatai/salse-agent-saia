"""
SAIA API Views
متوافقة مع django_ai_assistant API structure
تستخدم Django Ninja
"""
import logging
from typing import List, Optional
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.http import Http404
from ninja import NinjaAPI
from ninja.security import django_auth

from .schemas import (
    AssistantSchema,
    ThreadSchema,
    ThreadCreateSchema,
    MessageSchema,
    MessageCreateSchema,
    MessageResponseSchema,
    ErrorSchema,
)
from ..helpers import use_cases
from ..models import Thread, Message

logger = logging.getLogger(__name__)

# إنشاء API instance
api = NinjaAPI(
    title="SAIA Insurance AI API",
    version="2.0.0",
    urls_namespace="saia_ai_api",
    # يمكن تفعيل المصادقة لاحقاً
    # auth=django_auth,
    # csrf=True,
)


# ==================== Assistants ====================

@api.get(
    "/assistants/",
    response=List[AssistantSchema],
    tags=["assistants"],
    summary="قائمة المساعدين المتاحين"
)
def list_assistants(request):
    """الحصول على قائمة المساعدين المسجلين"""
    return use_cases.get_assistants_info(user=request.user, request=request)


@api.get(
    "/assistants/{assistant_id}/",
    response=AssistantSchema,
    tags=["assistants"],
    summary="معلومات مساعد محدد"
)
def get_assistant(request, assistant_id: str):
    """الحصول على معلومات مساعد بالـ ID"""
    info = use_cases.get_single_assistant_info(
        assistant_id=assistant_id,
        user=request.user,
        request=request
    )
    if not info:
        raise Http404(f"Assistant '{assistant_id}' not found")
    return info


# ==================== Threads ====================

@api.get(
    "/threads/",
    response=List[ThreadSchema],
    tags=["threads"],
    summary="قائمة المحادثات"
)
def list_threads(request, assistant_id: Optional[str] = None):
    """الحصول على قائمة المحادثات"""
    return use_cases.get_threads(
        user=request.user,
        assistant_id=assistant_id
    )


@api.post(
    "/threads/",
    response=ThreadSchema,
    tags=["threads"],
    summary="إنشاء محادثة جديدة"
)
def create_thread(request, payload: ThreadCreateSchema):
    """إنشاء محادثة جديدة"""
    return use_cases.create_thread(
        name=payload.name,
        assistant_id=payload.assistant_id,
        user=request.user,
        request=request
    )


@api.get(
    "/threads/{thread_id}/",
    response=ThreadSchema,
    tags=["threads"],
    summary="معلومات محادثة"
)
def get_thread(request, thread_id: int):
    """الحصول على معلومات محادثة"""
    thread = use_cases.get_single_thread(
        thread_id=thread_id,
        user=request.user,
        request=request
    )
    if not thread:
        raise Http404(f"Thread {thread_id} not found")
    return thread


@api.patch(
    "/threads/{thread_id}/",
    response=ThreadSchema,
    tags=["threads"],
    summary="تحديث محادثة"
)
def update_thread(request, thread_id: int, payload: ThreadCreateSchema):
    """تحديث اسم المحادثة"""
    thread = get_object_or_404(Thread, id=thread_id)
    return use_cases.update_thread(
        thread=thread,
        name=payload.name,
        user=request.user,
        request=request
    )


@api.delete(
    "/threads/{thread_id}/",
    response={204: None},
    tags=["threads"],
    summary="حذف محادثة"
)
def delete_thread(request, thread_id: int):
    """حذف محادثة"""
    thread = get_object_or_404(Thread, id=thread_id)
    use_cases.delete_thread(
        thread=thread,
        user=request.user,
        request=request
    )
    return 204, None


# ==================== Messages ====================

@api.get(
    "/threads/{thread_id}/messages/",
    response=List[MessageSchema],
    tags=["messages"],
    summary="رسائل المحادثة"
)
def list_messages(request, thread_id: int):
    """الحصول على رسائل المحادثة"""
    thread = get_object_or_404(Thread, id=thread_id)
    return use_cases.get_thread_messages(
        thread=thread,
        user=request.user,
        request=request
    )


@api.post(
    "/threads/{thread_id}/messages/",
    response={201: MessageResponseSchema},
    tags=["messages"],
    summary="إرسال رسالة"
)
async def create_message(request, thread_id: int, payload: MessageCreateSchema):
    """
    إرسال رسالة جديدة والحصول على رد المساعد
    """
    from asgiref.sync import sync_to_async
    
    @sync_to_async
    def get_thread():
        return get_object_or_404(Thread, id=thread_id)
    
    thread = await get_thread()
    
    result = await use_cases.create_message(
        assistant_id=payload.assistant_id,
        thread=thread,
        user=request.user,
        content=payload.content,
        phone=payload.phone,
        request=request
    )
    
    return 201, result


@api.delete(
    "/threads/{thread_id}/messages/{message_id}/",
    response={204: None},
    tags=["messages"],
    summary="حذف رسالة"
)
def delete_message(request, thread_id: int, message_id: int):
    """حذف رسالة"""
    message = get_object_or_404(Message, id=message_id, thread_id=thread_id)
    use_cases.delete_message(
        message=message,
        user=request.user,
        request=request
    )
    return 204, None


# ==================== Quick Chat (Legacy Support) ====================

@api.post(
    "/chat/",
    response=MessageResponseSchema,
    tags=["chat"],
    summary="محادثة سريعة (بدون thread)"
)
async def quick_chat(request, payload: MessageCreateSchema):
    """
    إرسال رسالة سريعة بدون إنشاء thread
    للتوافق مع الـ API القديم
    """
    result = await use_cases.quick_chat(
        assistant_id=payload.assistant_id,
        content=payload.content,
        phone=payload.phone,
        user=request.user,
        request=request
    )
    
    return result
