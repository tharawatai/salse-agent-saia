"""
Context Models - نماذج السياق المشتركة
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

from .ai_intent_analyzer import ConversationStage


@dataclass
class ConversationContext:
    """سياق المحادثة"""
    conversation_id: str
    user: Optional[Any] = None  # User model
    phone: Optional[str] = None
    current_stage: ConversationStage = ConversationStage.GREETING
    
    # البيانات المجمعة
    profile_data: Dict[str, Any] = field(default_factory=dict)
    vehicle_data: Dict[str, Any] = field(default_factory=dict)
    
    # العروض والاختيار
    offers_shown: List[Dict] = field(default_factory=list)
    selected_offer_id: Optional[int] = None
    selected_offer: Optional[Dict] = None
    
    # تدفق الطلب
    order_id: Optional[int] = None
    invoice_id: Optional[int] = None
    policy_id: Optional[int] = None
    
    # التتبع
    last_question: Optional[str] = None
    awaiting_input_type: Optional[str] = None
    retry_count: int = 0
    
    # سجل الرسائل
    messages: List[Dict] = field(default_factory=list)
    
    # 🆕 البيانات المحفوظة من الجلسات السابقة (للاستخدام عند الطلب)
    _saved_profile: Dict[str, Any] = field(default_factory=dict)
    _saved_vehicle: Dict[str, Any] = field(default_factory=dict)
    
    # الطوابع الزمنية
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_message_at: datetime = field(default_factory=datetime.now)
    
    def has_saved_data(self) -> bool:
        """هل يوجد بيانات محفوظة من جلسات سابقة؟"""
        return bool(self._saved_profile) or bool(self._saved_vehicle)
    
    def restore_saved_profile(self):
        """استعادة البيانات الشخصية المحفوظة"""
        if self._saved_profile:
            self.profile_data = self._saved_profile.copy()
            return True
        return False
    
    def restore_saved_vehicle(self):
        """استعادة بيانات السيارة المحفوظة"""
        if self._saved_vehicle:
            self.vehicle_data = self._saved_vehicle.copy()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user.id if self.user else None,
            'phone': self.phone,
            'current_stage': self.current_stage.value,
            'profile_data': self.profile_data,
            'vehicle_data': self.vehicle_data,
            'offers_shown': self.offers_shown,
            'selected_offer_id': self.selected_offer_id,
            'selected_offer': self.selected_offer,
            'order_id': self.order_id,
            'invoice_id': self.invoice_id,
            'policy_id': self.policy_id,
        }
