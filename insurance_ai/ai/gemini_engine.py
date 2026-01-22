"""
SmartGeminiEngine - محرك Gemini الذكي
يولد كل الردود ديناميكياً مع تحسينات الأداء
"""
import json
import logging
import os
from typing import Dict, Any, List

import google.generativeai as genai
from django.conf import settings
from asgiref.sync import sync_to_async

from .retry import retry_with_backoff
from .prompts import (
    build_smart_prompt, 
    is_advisory_question, 
    is_comparison_question,
    get_smart_recommendation,
    get_comparison_response
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Gemini Structured Output Schema - الذكاء يقرر كل شيء
# ═══════════════════════════════════════════════════════════════

SMART_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "user_intent": {
            "type": "string",
            "description": "نية المستخدم المفهومة من الرسالة"
        },
        "is_positive_response": {
            "type": "boolean",
            "description": "هل رد المستخدم إيجابي (موافقة/تأكيد) أم سلبي (رفض/تعديل)؟"
        },
        "should_move_to_next_stage": {
            "type": "boolean",
            "description": "هل يجب الانتقال للمرحلة التالية؟"
        },
        "recommended_next_stage": {
            "type": "string",
            "description": "المرحلة التالية المقترحة"
        },
        "ai_response": {
            "type": "string", 
            "description": "الرد الذكي والمناسب للعميل بالعربية"
        },
        "extracted_vehicle_brand": {"type": "string", "description": "ماركة السيارة المستخرجة"},
        "extracted_vehicle_model": {"type": "string", "description": "موديل السيارة المستخرج"},
        "extracted_vehicle_year": {"type": "integer", "description": "سنة الصنع المستخرجة"},
        "extracted_vehicle_value": {"type": "number", "description": "قيمة السيارة المستخرجة"},
        "extracted_plate_number": {"type": "string", "description": "رقم اللوحة المستخرج"},
        "extracted_national_id": {"type": "string", "description": "رقم الهوية المستخرج"},
        "extracted_birth_date": {"type": "string", "description": "تاريخ الميلاد المستخرج"},
        "extracted_service_type": {"type": "string", "description": "نوع التأمين: comprehensive أو tpl"},
        "selected_offer_number": {"type": "integer", "description": "رقم العرض المختار (1-based)"},
        "is_data_complete": {
            "type": "boolean",
            "description": "هل البيانات المطلوبة للمرحلة الحالية مكتملة؟"
        },
        "modification_request": {
            "type": "string",
            "enum": ["none", "cancel", "edit_vehicle", "edit_profile", "change_offer", "go_back"],
            "description": "نوع طلب التعديل: none=لا يوجد، cancel=إلغاء كامل، edit_vehicle=تعديل السيارة، edit_profile=تعديل البيانات الشخصية، change_offer=تغيير العرض، go_back=رجوع للخطوة السابقة"
        },
        "wants_to_restart": {
            "type": "boolean",
            "description": "هل يريد العميل البدء من جديد أو إلغاء العملية؟"
        },
        "field_to_edit": {
            "type": "string",
            "enum": ["none", "brand", "model", "year", "value", "plate_no", "national_id", "birth_date"],
            "description": "الحقل المحدد للتعديل إذا طلب المستخدم تعديل حقل معين. مثال: 'لا اللوحة غلط' → plate_no، 'الماركة خطأ' → brand، 'رقم الهوية غير صحيح' → national_id"
        },
        "is_partial_correction": {
            "type": "boolean",
            "description": "هل المستخدم يريد تصحيح حقل واحد فقط مع الاحتفاظ بباقي البيانات؟ مثال: 'لا غير صحيحة اسم اللوحة' = true"
        }
    },
    "required": ["user_intent", "is_positive_response", "should_move_to_next_stage", "ai_response", "is_data_complete", "modification_request", "wants_to_restart", "field_to_edit", "is_partial_correction"]
}


# المراحل الصالحة
VALID_STAGES = {
    'greeting', 'service_details', 'collecting_vehicle', 'confirming_vehicle',
    'showing_offers', 'offer_details', 'collecting_profile', 'confirming_profile',
    'order_summary', 'confirmation', 'payment_pending', 'completed'
}


class SmartGeminiEngine:
    """محرك Gemini الذكي - يولد كل الردود ديناميكياً مع تحسينات الأداء"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not self.api_key:
            self.api_key = os.environ.get('GEMINI_API_KEY', '')
        
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY not configured!")
        
        genai.configure(api_key=self.api_key)
        
        self.smart_model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=SMART_ANALYSIS_SCHEMA,
                temperature=0.4,
            )
        )
        
        # نموذج للردود البسيطة
        self.simple_model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            generation_config=genai.GenerationConfig(
                temperature=0.7,
            )
        )
        
        logger.info("✅ SmartGeminiEngine initialized - Full AI Mode with optimizations")
    
    async def process_with_ai(
        self,
        message: str,
        current_stage: str,
        context_data: Dict[str, Any],
        available_offers: List[Dict] = None,
        available_services: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        معالجة الرسالة بالكامل باستخدام الذكاء الاصطناعي مع retry
        
        Args:
            message: رسالة العميل
            current_stage: المرحلة الحالية
            context_data: بيانات السياق
            available_offers: العروض المتاحة
            available_services: الخدمات المتاحة من قاعدة البيانات
        
        Returns:
            Dict: نتيجة التحليل
        """
        
        # 🆕 الكشف المبكر عن الأسئلة الاستشارية
        is_advisory = is_advisory_question(message)
        is_comparison = is_comparison_question(message)
        
        if is_advisory or is_comparison:
            logger.info(f"🧠 Detected advisory/comparison question: advisory={is_advisory}, comparison={is_comparison}")
        
        # 🆕 جلب الخدمات من قاعدة البيانات إذا لم تُمرر
        if available_services is None:
            try:
                from ..database_manager import database_manager
                available_services = await sync_to_async(database_manager.get_insurance_services)()
                logger.debug(f"📋 Loaded {len(available_services)} services from DB")
            except Exception as e:
                logger.warning(f"⚠️ Could not load services: {e}")
                available_services = []
        
        prompt = build_smart_prompt(message, current_stage, context_data, available_offers, available_services)
        
        async def _call_gemini():
            response = await sync_to_async(self.smart_model.generate_content)(prompt)
            return json.loads(response.text)
        
        try:
            result = await retry_with_backoff(_call_gemini)
            
            # التحقق من صحة المرحلة المقترحة
            recommended_stage = result.get('recommended_next_stage', current_stage)
            if recommended_stage not in VALID_STAGES:
                logger.warning(f"⚠️ Invalid stage from AI: {recommended_stage}, keeping {current_stage}")
                result['recommended_next_stage'] = current_stage
                result['should_move_to_next_stage'] = False
            
            # 🆕 تحسين الرد للأسئلة الاستشارية إذا كان الرد يكرر القائمة
            if is_advisory or is_comparison:
                ai_response = result.get('ai_response', '')
                # الكشف عن التكرار (إذا كان الرد يحتوي على قائمة الخدمات فقط)
                if self._is_repetitive_response(ai_response):
                    logger.info("🔄 Detected repetitive response, enhancing...")
                    vehicle_data = context_data.get('vehicle', {})
                    if is_comparison:
                        result['ai_response'] = get_comparison_response()
                    else:
                        result['ai_response'] = get_smart_recommendation(
                            vehicle_year=vehicle_data.get('year'),
                            vehicle_value=vehicle_data.get('value')
                        )
                    result['should_move_to_next_stage'] = False
            
            logger.info(f"🤖 AI Decision: intent={result.get('user_intent')}, positive={result.get('is_positive_response')}, next={result.get('recommended_next_stage')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini error after retries: {e}")
            return self._get_fallback_response(current_stage)
    
    def _is_repetitive_response(self, response: str) -> bool:
        """
        الكشف عن الردود المكررة (قائمة الخدمات فقط)
        
        Args:
            response: الرد
        
        Returns:
            bool: True إذا كان الرد مكرر
        """
        # الكلمات التي تدل على تكرار القائمة
        repetitive_patterns = [
            'لدينا:',
            'نوفر:',
            'خدماتنا:',
            '1. تأمين شامل',
            '2. تأمين ضد الغير',
            '3. تأمين شامل بلس',
            'ما هو نوع التأمين الذي تفكر فيه',
            'هل أنت مهتم بأي نوع معين',
        ]
        
        response_lower = response.lower()
        matches = sum(1 for pattern in repetitive_patterns if pattern.lower() in response_lower)
        
        # إذا كان الرد يحتوي على 3 أو أكثر من هذه الأنماط، فهو مكرر
        return matches >= 3
    
    async def generate_simple_response(self, prompt: str) -> str:
        """
        توليد رد بسيط من Gemini
        
        Args:
            prompt: الـ prompt
        
        Returns:
            str: الرد
        """
        async def _call():
            response = await sync_to_async(self.simple_model.generate_content)(prompt)
            return response.text.strip()
        
        try:
            return await retry_with_backoff(_call)
        except Exception as e:
            logger.error(f"❌ Simple response error: {e}")
            return "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى."
    
    def _get_fallback_response(self, stage: str) -> Dict[str, Any]:
        """رد احتياطي في حالة فشل Gemini"""
        return {
            "user_intent": "unknown",
            "is_positive_response": False,
            "should_move_to_next_stage": False,
            "recommended_next_stage": stage,
            "ai_response": "عذراً، لم أفهم. هل يمكنك إعادة صياغة طلبك؟",
            "is_data_complete": False,
            "modification_request": "none",
            "wants_to_restart": False,
            "field_to_edit": "none",
            "is_partial_correction": False
        }
