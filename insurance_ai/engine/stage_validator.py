"""
StageValidator - التحقق من صحة الانتقال بين المراحل
"""
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Whitelist للمراحل الصالحة
# ═══════════════════════════════════════════════════════════════

VALID_STAGES = {
    'greeting', 'service_details', 'collecting_vehicle', 'confirming_vehicle',
    'showing_offers', 'offer_details', 'collecting_profile', 'confirming_profile',
    'order_summary', 'confirmation', 'payment_pending', 'completed'
}

# خريطة الانتقالات المسموحة (من -> إلى)
# تم تحديثها لدعم: التعديل، الرجوع، الإلغاء
VALID_TRANSITIONS = {
    'greeting': {'service_details', 'collecting_vehicle'},
    'service_details': {'collecting_vehicle', 'greeting'},  # + رجوع
    'collecting_vehicle': {'confirming_vehicle', 'greeting'},  # + إلغاء
    'confirming_vehicle': {'showing_offers', 'collecting_vehicle', 'greeting'},  # + تعديل + إلغاء
    'showing_offers': {'offer_details', 'collecting_vehicle', 'greeting'},  # + تعديل السيارة + إلغاء
    'offer_details': {'collecting_profile', 'showing_offers', 'collecting_vehicle', 'greeting'},  # + رجوع + تعديل + إلغاء
    'collecting_profile': {'confirming_profile', 'showing_offers', 'collecting_vehicle', 'greeting'},  # + رجوع + تعديل + إلغاء
    'confirming_profile': {'order_summary', 'collecting_profile', 'showing_offers', 'greeting'},  # + تعديل + رجوع + إلغاء
    'order_summary': {'confirmation', 'collecting_profile', 'showing_offers', 'collecting_vehicle', 'greeting'},  # + تعديل كل شيء + إلغاء
    'confirmation': {'payment_pending', 'order_summary', 'greeting'},  # + رجوع + إلغاء
    'payment_pending': {'completed', 'greeting'},  # + إلغاء
    'completed': {'greeting'}
}


class StageValidator:
    """التحقق المحلي من صحة الانتقال بين المراحل"""
    
    # الحقول المطلوبة لكل مرحلة
    STAGE_REQUIREMENTS = {
        'greeting': [],
        'service_details': [],
        'collecting_vehicle': ['brand', 'model', 'year', 'value', 'plate_no'],
        'confirming_vehicle': [],
        'showing_offers': [],
        'offer_details': ['selected_offer_id'],
        'collecting_profile': ['national_id', 'birth_date'],
        'confirming_profile': [],
        'order_summary': [],
        'confirmation': [],
        'payment_pending': ['order_id', 'invoice_id'],
        'completed': ['policy_id'],
    }
    
    @classmethod
    def validate_transition(
        cls,
        current_stage: str,
        next_stage: str,
        context: 'ConversationContext'
    ) -> Tuple[bool, str]:
        """
        التحقق من صحة الانتقال
        
        Args:
            current_stage: المرحلة الحالية
            next_stage: المرحلة التالية
            context: سياق المحادثة
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # تحقق من صحة المرحلة التالية
        if next_stage not in VALID_STAGES:
            return False, f"مرحلة غير صالحة: {next_stage}"
        
        # تحقق من أن الانتقال مسموح
        allowed_next = VALID_TRANSITIONS.get(current_stage, set())
        if next_stage not in allowed_next and next_stage != current_stage:
            return False, f"انتقال غير مسموح من {current_stage} إلى {next_stage}"
        
        # تحقق من اكتمال البيانات المطلوبة للمرحلة الحالية
        required = cls.STAGE_REQUIREMENTS.get(current_stage, [])
        missing = cls._get_missing_fields(required, context)
        
        if missing and next_stage != current_stage:
            return False, f"بيانات ناقصة: {', '.join(missing)}"
        
        return True, ""
    
    @classmethod
    def _get_missing_fields(cls, required: List[str], context: 'ConversationContext') -> List[str]:
        """الحصول على الحقول الناقصة"""
        missing = []
        for field in required:
            if field in ['brand', 'model', 'year', 'value', 'plate_no']:
                if not context.vehicle_data.get(field):
                    missing.append(field)
            elif field in ['national_id', 'birth_date']:
                if not context.profile_data.get(field):
                    missing.append(field)
            elif field == 'selected_offer_id':
                if not context.selected_offer_id:
                    missing.append(field)
            elif field == 'order_id':
                if not context.order_id:
                    missing.append(field)
            elif field == 'invoice_id':
                if not context.invoice_id:
                    missing.append(field)
            elif field == 'policy_id':
                if not context.policy_id:
                    missing.append(field)
        return missing
    
    @classmethod
    def get_completion_status(cls, stage: str, context: 'ConversationContext') -> Dict[str, Any]:
        """
        حالة اكتمال المرحلة
        
        Args:
            stage: المرحلة
            context: سياق المحادثة
        
        Returns:
            Dict: معلومات الاكتمال
        """
        required = cls.STAGE_REQUIREMENTS.get(stage, [])
        missing = cls._get_missing_fields(required, context)
        
        return {
            'stage': stage,
            'required_fields': required,
            'missing_fields': missing,
            'is_complete': len(missing) == 0,
            'completion_percentage': ((len(required) - len(missing)) / len(required) * 100) if required else 100
        }
    
    @classmethod
    def get_next_stage(cls, current_stage: str) -> str:
        """
        الحصول على المرحلة التالية الافتراضية
        
        Args:
            current_stage: المرحلة الحالية
        
        Returns:
            str: المرحلة التالية
        """
        STAGE_FLOW = {
            'greeting': 'service_details',
            'service_details': 'collecting_vehicle',
            'collecting_vehicle': 'confirming_vehicle',
            'confirming_vehicle': 'showing_offers',
            'showing_offers': 'offer_details',
            'offer_details': 'collecting_profile',
            'collecting_profile': 'confirming_profile',
            'confirming_profile': 'order_summary',
            'order_summary': 'confirmation',
            'confirmation': 'payment_pending',
            'payment_pending': 'completed',
            'completed': 'greeting'
        }
        return STAGE_FLOW.get(current_stage, 'greeting')
    
    @classmethod
    def get_previous_stage(cls, current_stage: str) -> str:
        """
        الحصول على المرحلة السابقة
        
        Args:
            current_stage: المرحلة الحالية
        
        Returns:
            str: المرحلة السابقة
        """
        BACK_FLOW = {
            'service_details': 'greeting',
            'collecting_vehicle': 'greeting',
            'confirming_vehicle': 'collecting_vehicle',
            'showing_offers': 'confirming_vehicle',
            'offer_details': 'showing_offers',
            'collecting_profile': 'offer_details',
            'confirming_profile': 'collecting_profile',
            'order_summary': 'confirming_profile',
            'confirmation': 'order_summary',
            'payment_pending': 'confirmation',
            'completed': 'greeting',
            'greeting': 'greeting'
        }
        return BACK_FLOW.get(current_stage, 'greeting')
