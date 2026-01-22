"""
SessionManager - مدير الجلسات
مع تحسينات الأداء - Cache First Strategy
"""
import logging
from datetime import datetime
from typing import Optional, Dict

from asgiref.sync import sync_to_async

from insurance_core.models import User
from whatsapp_integration.models import WhatsAppSession
from ..context_models import ConversationContext
from ..ai_intent_analyzer import ConversationStage
from .context_store import get_context_store, VALID_STAGES

logger = logging.getLogger(__name__)


# 🆕 مراحل تتطلب حفظ في DB
PERSIST_STAGES = {
    'confirming_vehicle',  # بعد تأكيد بيانات السيارة
    'confirming_profile',  # بعد تأكيد البيانات الشخصية
    'payment_pending',     # بعد إنشاء الطلب
    'completed',           # بعد إصدار الوثيقة
}


class SessionManager:
    """
    مدير الجلسات - Cache First Strategy
    
    استراتيجية الأداء:
    - القراءة: الكاش أولاً، ثم DB
    - الكتابة: الكاش دائماً، DB فقط عند المراحل المهمة
    """
    
    @staticmethod
    async def get_or_create_context(
        conversation_id: str,
        phone: str = None,
        user: User = None
    ) -> ConversationContext:
        """
        الحصول على أو إنشاء سياق المحادثة
        Cache First - سريع جداً
        """
        context_store = get_context_store()
        
        # 1️⃣ محاولة جلب من الكاش (سريع جداً)
        ctx = context_store.get(conversation_id)
        if ctx:
            logger.debug(f"⚡ Cache hit: {conversation_id[:8]}...")
            return ctx
        
        # 2️⃣ محاولة جلب من DB (فقط إذا لم يكن في الكاش)
        if phone:
            try:
                session = await sync_to_async(
                    WhatsAppSession.objects.filter(phone_number=phone).first
                )()
                
                if session and session.context_data:
                    ctx = SessionManager._restore_context(conversation_id, session.context_data, phone, user)
                    context_store.set(conversation_id, ctx)
                    logger.info(f"📦 DB → Cache: {conversation_id[:8]}...")
                    return ctx
            except Exception as e:
                logger.warning(f"⚠️ DB load error: {e}")
        
        # 3️⃣ إنشاء سياق جديد
        ctx = ConversationContext(
            conversation_id=conversation_id,
            phone=phone,
            user=user,
            current_stage=ConversationStage.GREETING
        )
        context_store.set(conversation_id, ctx)
        logger.info(f"🆕 New context: {conversation_id[:8]}...")
        return ctx
    
    @staticmethod
    def _restore_context(
        conversation_id: str,
        data: Dict,
        phone: str = None,
        user: User = None
    ) -> ConversationContext:
        """استعادة السياق من البيانات"""
        stage_value = data.get('current_stage', 'greeting')
        
        if stage_value not in VALID_STAGES:
            stage_value = 'greeting'
        
        # إذا كانت المرحلة السابقة completed، نبدأ من جديد
        if stage_value == 'completed':
            logger.info(f"🔄 Previous session completed, starting fresh")
            return ConversationContext(
                conversation_id=conversation_id,
                phone=phone,
                user=user,
                current_stage=ConversationStage.GREETING,
                _saved_profile=data.get('profile_data', {}),
                _saved_vehicle=data.get('vehicle_data', {}),
            )
        
        try:
            stage = ConversationStage(stage_value)
        except ValueError:
            stage = ConversationStage.GREETING
        
        return ConversationContext(
            conversation_id=conversation_id,
            phone=phone,
            user=user,
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
    
    @staticmethod
    async def save_context(context: ConversationContext, force_db: bool = False):
        """
        حفظ السياق - Cache First
        
        Args:
            context: السياق
            force_db: إجبار الحفظ في DB
        """
        context_store = get_context_store()
        
        # 1️⃣ حفظ في الكاش دائماً (سريع جداً)
        context_store.set(context.conversation_id, context)
        context.updated_at = datetime.now()
        
        # 2️⃣ حفظ في DB فقط عند المراحل المهمة أو بالإجبار
        should_persist = force_db or context.current_stage.value in PERSIST_STAGES
        
        if should_persist and context.phone:
            await SessionManager._persist_to_db(context)
    
    @staticmethod
    async def _persist_to_db(context: ConversationContext):
        """حفظ في قاعدة البيانات (عملية ثقيلة)"""
        try:
            session = await sync_to_async(
                WhatsAppSession.objects.filter(phone_number=context.phone).first
            )()
            
            if session:
                session.context_data = {
                    'current_stage': context.current_stage.value,
                    'profile_data': context.profile_data,
                    'vehicle_data': context.vehicle_data,
                    'offers_shown': context.offers_shown,
                    'selected_offer_id': context.selected_offer_id,
                    'selected_offer': context.selected_offer,
                    'order_id': context.order_id,
                    'invoice_id': context.invoice_id,
                    'policy_id': context.policy_id,
                }
                session.current_stage = context.current_stage.value
                await sync_to_async(session.save)()
                logger.info(f"💾 Persisted to DB: {context.phone}")
        except Exception as e:
            logger.warning(f"⚠️ DB save error: {e}")
    
    @staticmethod
    async def delete_context(conversation_id: str):
        """حذف السياق"""
        context_store = get_context_store()
        context_store.delete(conversation_id)
        logger.info(f"🗑️ Context deleted: {conversation_id[:8]}...")
