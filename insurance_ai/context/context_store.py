"""
ContextStore - مخزن السياقات (Redis/Memory)
"""
import json
import logging
from typing import Optional, Dict

from django.conf import settings

from ..context_models import ConversationContext
from ..ai_intent_analyzer import ConversationStage

logger = logging.getLogger(__name__)


# المراحل الصالحة
VALID_STAGES = {
    'greeting', 'service_details', 'collecting_vehicle', 'confirming_vehicle',
    'showing_offers', 'offer_details', 'collecting_profile', 'confirming_profile',
    'order_summary', 'confirmation', 'payment_pending', 'completed'
}


class ContextStore:
    """مخزن السياقات - يدعم Redis مع fallback للذاكرة"""
    
    def __init__(self):
        self._memory_store: Dict[str, ConversationContext] = {}
        self._redis_client = None
        self._use_redis = False
        self._init_redis()
    
    def _init_redis(self):
        """محاولة الاتصال بـ Redis"""
        try:
            import redis
            redis_url = getattr(settings, 'REDIS_URL', None)
            if redis_url:
                self._redis_client = redis.from_url(redis_url)
                self._redis_client.ping()
                self._use_redis = True
                logger.info("✅ Redis connected for context storage")
            else:
                logger.info("ℹ️ REDIS_URL not configured, using memory store")
        except ImportError:
            logger.info("ℹ️ Redis package not installed, using memory store")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}, using memory store")
    
    @property
    def is_redis_connected(self) -> bool:
        """هل Redis متصل؟"""
        return self._use_redis
    
    def get(self, key: str) -> Optional[ConversationContext]:
        """جلب سياق"""
        if self._use_redis:
            try:
                data = self._redis_client.get(f"ctx:{key}")
                if data:
                    return self._deserialize(json.loads(data))
            except Exception as e:
                logger.warning(f"⚠️ Redis get error: {e}")
        
        return self._memory_store.get(key)
    
    def set(self, key: str, context: ConversationContext, ttl: int = 86400):
        """حفظ سياق (TTL افتراضي 24 ساعة)"""
        self._memory_store[key] = context
        
        if self._use_redis:
            try:
                data = json.dumps(self._serialize(context))
                self._redis_client.setex(f"ctx:{key}", ttl, data)
            except Exception as e:
                logger.warning(f"⚠️ Redis set error: {e}")
    
    def delete(self, key: str):
        """حذف سياق"""
        self._memory_store.pop(key, None)
        
        if self._use_redis:
            try:
                self._redis_client.delete(f"ctx:{key}")
            except Exception as e:
                logger.warning(f"⚠️ Redis delete error: {e}")
    
    def _serialize(self, ctx: ConversationContext) -> Dict:
        """تحويل السياق لـ JSON"""
        return {
            'conversation_id': ctx.conversation_id,
            'phone': ctx.phone,
            'current_stage': ctx.current_stage.value,
            'profile_data': ctx.profile_data,
            'vehicle_data': ctx.vehicle_data,
            'offers_shown': ctx.offers_shown,
            'selected_offer_id': ctx.selected_offer_id,
            'selected_offer': ctx.selected_offer,
            'order_id': ctx.order_id,
            'invoice_id': ctx.invoice_id,
            'policy_id': ctx.policy_id,
        }
    
    def _deserialize(self, data: Dict) -> ConversationContext:
        """تحويل JSON لسياق"""
        stage_value = data.get('current_stage', 'greeting')
        
        # التحقق من صحة المرحلة
        if stage_value not in VALID_STAGES:
            logger.warning(f"⚠️ Invalid stage in store: {stage_value}, resetting to greeting")
            stage_value = 'greeting'
        
        try:
            stage = ConversationStage(stage_value)
        except ValueError:
            stage = ConversationStage.GREETING
        
        return ConversationContext(
            conversation_id=data.get('conversation_id', ''),
            phone=data.get('phone'),
            current_stage=stage,
            profile_data=data.get('profile_data', {}),
            vehicle_data=data.get('vehicle_data', {}),
            offers_shown=data.get('offers_shown', []),
            selected_offer_id=data.get('selected_offer_id'),
            selected_offer=data.get('selected_offer'),
            order_id=data.get('order_id'),
            invoice_id=data.get('invoice_id'),
            policy_id=data.get('policy_id'),
        )


# Global context store
_context_store: Optional[ContextStore] = None


def get_context_store() -> ContextStore:
    """الحصول على instance من مخزن السياقات"""
    global _context_store
    if _context_store is None:
        _context_store = ContextStore()
    return _context_store


def reset_context_store():
    """إعادة تعيين مخزن السياقات"""
    global _context_store
    _context_store = None
    logger.info("🔄 Context store reset")
