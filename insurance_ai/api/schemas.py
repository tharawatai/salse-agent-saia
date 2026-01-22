"""
API Schemas - Pydantic/Ninja schemas
متوافقة مع django_ai_assistant
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from ninja import Schema


# ==================== Assistants ====================

class AssistantSchema(Schema):
    """معلومات المساعد"""
    id: str
    name: str
    model: str = "gemini-2.0-flash"


# ==================== Threads ====================

class ThreadSchema(Schema):
    """معلومات المحادثة"""
    id: int
    name: str
    assistant_id: str
    created_at: datetime
    updated_at: datetime


class ThreadCreateSchema(Schema):
    """إنشاء/تحديث محادثة"""
    name: str = ""
    assistant_id: str = "insurance-assistant"


# ==================== Messages ====================

class MessageSchema(Schema):
    """معلومات الرسالة"""
    id: int
    type: str
    content: str
    created_at: datetime
    extra_data: Dict[str, Any] = {}


class MessageCreateSchema(Schema):
    """إنشاء رسالة"""
    assistant_id: str = "insurance-assistant"
    content: str
    phone: Optional[str] = None


class MessageResponseSchema(Schema):
    """رد على الرسالة"""
    success: bool
    response: str
    stage: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    has_invoice: bool = False
    invoice_url: Optional[str] = None
    has_policy: bool = False
    policy_url: Optional[str] = None
    error: Optional[str] = None


# ==================== Errors ====================

class ErrorSchema(Schema):
    """رسالة خطأ"""
    message: str
    code: Optional[str] = None
