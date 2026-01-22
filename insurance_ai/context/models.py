"""
Context Models - نماذج السياق
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from ..ai_intent_analyzer import ConversationStage


@dataclass
class StageResult:
    """نتيجة معالجة المرحلة"""
    success: bool
    response_message: str
    next_stage: Optional[ConversationStage] = None
    data_collected: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    has_invoice: bool = False
    invoice_url: Optional[str] = None
    invoice_pdf_path: Optional[str] = None  # مسار ملف PDF للفاتورة
    has_policy: bool = False
    policy_url: Optional[str] = None
    policy_pdf_path: Optional[str] = None  # مسار ملف PDF للوثيقة
    show_offers: bool = False  # علامة لإعادة عرض العروض
