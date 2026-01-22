"""
AI Intent Analyzer - تحليل نية المستخدم بالذكاء الاصطناعي
يستبدل جميع الكلمات الثابتة بتحليل ذكي باستخدام Google Gemini
"""
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


class ConversationStage(Enum):
    """مراحل المحادثة"""
    GREETING = "greeting"
    SELECTING_SERVICE = "selecting_service"
    SERVICE_DETAILS = "service_details"
    COLLECTING_VEHICLE = "collecting_vehicle"
    CONFIRMING_VEHICLE = "confirming_vehicle"
    SHOWING_OFFERS = "showing_offers"
    OFFER_DETAILS = "offer_details"
    COLLECTING_PROFILE = "collecting_profile"
    CONFIRMING_PROFILE = "confirming_profile"
    ORDER_SUMMARY = "order_summary"
    CONFIRMATION = "confirmation"
    PAYMENT_PENDING = "payment_pending"
    COMPLETED = "completed"


class UserIntent(str, Enum):
    """أنواع نوايا المستخدم"""
    GREETING = "greeting"
    ASK_SERVICES = "ask_services"
    SELECT_SERVICE = "select_service"
    PROVIDE_PROFILE_DATA = "provide_profile_data"
    PROVIDE_VEHICLE_DATA = "provide_vehicle_data"
    SELECT_OFFER = "select_offer"
    CONFIRM = "confirm"
    REJECT = "reject"
    CANCEL = "cancel"
    MODIFY = "modify"
    ASK_QUESTION = "ask_question"
    ASK_HISTORY = "ask_history"
    RESUME = "resume"
    UNKNOWN = "unknown"


@dataclass
class IntentAnalysisResult:
    """نتيجة تحليل النية"""
    intent: UserIntent
    confidence: float
    extracted_data: Dict[str, Any]
    should_transition: bool
    next_stage: Optional[ConversationStage]
    response_hint: str
    raw_response: str = ""


class AIIntentAnalyzer:
    """محلل النية الذكي باستخدام Gemini"""
    
    def __init__(self):
        self.model = None
        self.model_id = 'gemini-2.0-flash-exp'
        self._init_model()
    
    def _init_model(self):
        """Initialize Gemini model"""
        try:
            gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel(self.model_id)
                logger.info("AI Intent Analyzer initialized with google.generativeai")
            else:
                logger.warning("GEMINI_API_KEY not found - AI analysis disabled")
        except Exception as e:
            logger.error(f"AI Intent Analyzer init error: {e}")
    
    def analyze(
        self,
        message: str,
        current_stage: ConversationStage,
        context_data: Dict[str, Any],
        available_services: List[Dict] = None
    ) -> IntentAnalysisResult:
        """
        تحليل نية المستخدم بالذكاء الاصطناعي
        
        Args:
            message: رسالة المستخدم
            current_stage: المرحلة الحالية
            context_data: البيانات المجمعة
            available_services: الخدمات المتوفرة من DB
        """
        if not self.model:
            return self._fallback_analysis(message, current_stage)
        
        try:
            prompt = self._build_analysis_prompt(
                message, current_stage, context_data, available_services
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=500,
                )
            )
            
            result = self._parse_response(response.text, message, current_stage)
            
            logger.info(f"[INTENT] AI Intent: {result.intent.value} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._fallback_analysis(message, current_stage)
    
    def _build_analysis_prompt(
        self,
        message: str,
        current_stage: ConversationStage,
        context_data: Dict,
        available_services: List[Dict] = None
    ) -> str:
        """بناء prompt محسن لتحليل النية"""
        
        services_text = ""
        if available_services:
            services_text = "\n".join([
                f"- {s.get('name_ar', s.get('code', ''))}: {s.get('description', '')}"
                for s in available_services
            ])
        
        collected_data = json.dumps(context_data, ensure_ascii=False, default=str)
        
        # تعليمات ذكية بناءً على المرحلة (بدون كلمات محددة)
        stage_context = {
            "greeting": "المستخدم في بداية المحادثة. قد يحيي، يسأل عن الخدمات، أو يطلب تأمين مباشرة.",
            "selecting_service": "المستخدم يختار نوع التأمين (شامل/ضد الغير/VIP).",
            "service_details": "شرح تفاصيل الخدمة المختارة واقناع العميل بها.",
            "collecting_vehicle": "جمع بيانات السيارة (النوع، الموديل، السنة، القيمة، اللوحة).",
            "confirming_vehicle": "المستخدم يؤكد أو يعدل بيانات السيارة المعروضة.",
            "showing_offers": "عرض العروض للمستخدم. ينتظر اختيار عرض برقم أو اسم شركة.",
            "offer_details": "تفاصيل العرض المختار. ينتظر موافقة أو رفض.",
            "collecting_profile": "جمع البيانات الشخصية (الهوية، تاريخ الميلاد).",
            "confirming_profile": "تأكيد البيانات الشخصية قبل الانتقال للملخص.",
            "order_summary": "ملخص الطلب الكامل. ينتظر التأكيد النهائي.",
            "confirmation": "تم تأكيد الطلب بنجاح وننتظر إصدار الفاتورة.",
            "payment_pending": "انتظار سداد الفاتورة.",
            "completed": "تم اكتمال الطلب وإصدار الوثيقة."
        }
        
        stage_desc = stage_context.get(current_stage.value, "مرحلة غير محددة")
        
        prompt = f"""أنت محلل نوايا ذكي جداً لنظام تأمين سيارات سعودي.
مهمتك: فهم نية المستخدم الحقيقية من رسالته وتصنيفها بدقة واستخراج البيانات بنجاح.

═══════════════════════════════════════
📍 السياق الحالي
═══════════════════════════════════════
• المرحلة الحالية: {current_stage.value}
• نوع المرحلة: {stage_desc}
• البيانات المجمعة: {collected_data}
{f'• الخدمات المتوفرة: {services_text}' if services_text else ''}

═══════════════════════════════════════
💬 رسالة المستخدم
═══════════════════════════════════════
"{message}"

═══════════════════════════════════════
🧠 تصنيفات النوايا (حلل المعنى وليس الكلمات!)
═══════════════════════════════════════

1. **greeting**: تحية أو دردشة بسيطة.
2. **ask_services**: سؤال عن الخدمات أو أنواع التأمين اللي عندكم.
3. **select_service**: اختيار نوع تأمين (شامل، ضد الغير، VIP).
4. **provide_vehicle_data**: تقديم بيانات عن السيارة (كامري، 2023، قيمتها 80 الف).
5. **provide_profile_data**: تقديم بيانات شخصية (هوية، ميلاد).
6. **select_offer**: اختيار عرض من العروض المعروضة (برقم العرض أو اسم الشركة).
7. **confirm**: موافقة وتأكيد (نعم، تمام، اوكي، كمل، استمر).
8. **reject**: رفض (لا، ما أبي، غيره، مو عاجبني).
9. **cancel**: طلب إلغاء صريح للعملية.
10. **modify**: طلب تعديل بيانات سابقة (أبي أعدل الموديل، غلطت في اللوحة).
11. **ask_question**: سؤال عام أو استفسار عن النظام.
12. **ask_history**: سؤال عن السجل السابق أو التأمينات السابقة.
13. **resume**: طلب استئناف طلب سابق.

═══════════════════════════════════════
🎯 قواعد التحليل الذكي
═══════════════════════════════════════

✅ افهم **المعنى العام** للرسالة وليس كلمات بعينها
✅ انتبه لـ **نبرة** الرسالة (إيجابية/سلبية/محايدة)
✅ إذا المستخدم يُعبر عن **رغبة صريحة بالإلغاء** = cancel
✅ ⚠️ الاستياء أو الغضب بدون طلب إلغاء ≠ cancel!
✅ إذا المستخدم يُعبر عن **الموافقة** أو **القبول** = confirm
✅ إذا المستخدم يسأل عن **معلومات سابقة** له = ask_history
✅ استخرج **كل البيانات** الموجودة في الرسالة

✅ **service_type**: يجب أن يكون حصراً (comprehensive أو tpl أو vip).
    - شامل/اصلاح وكالة = comprehensive
    - ضد الغير/طرف ثالث/إلزامي = tpl
    - VIP/بلاتيني = vip
✅ **confirmation**: يكون true إذا قال (نعم، تمام، موافق، أكمل) و false إذا قال (لا، توقف، إلغاء).

⛔ لا تعتمد على كلمات محددة - افهم السياق!
⛔ "لا اريد" في سياق رفض = cancel (وليس confirm)
⛔ "نعم" في سياق تأكيد = confirm
⛔ أرقام في سياق اختيار عرض = select_offer

✅ **brand/model/year**: استخرجها بدقة إذا ذكرت.
✅ **should_transition**: هل ننتقل للمرحلة التالية بناءً على النية واكتمال البيانات؟


═══════════════════════════════════════
📤 التنسيق المطلوب (JSON فقط)
═══════════════════════════════════════
{{
    "intent": "اسم النية بالإنجليزية",
    "confidence": 0.0-1.0,
    "reasoning": "سبب التحليل باختصار",
    "extracted_data": {{
        "service_type": "comprehensive/tpl/vip",
        "brand": "ماركة السيارة",
        "model": "الموديل",
        "year": "السنة",
        "value": "القيمة التقديرية (رقم)",
        "plate_no": "رقم اللوحة",
        "national_id": "رقم الهوية",
        "birth_date": "تاريخ الميلاد",
        "confirmation": true/false,
        "company_name": "اسم شركة التأمين المختارة",
        "offer_number": "رقم العرض المختار (رقم فقط)"
    }},
    "should_transition": true/false,
    "next_stage": "المرحلة المقترحة التالية (اختياري)"
}}

أرجع JSON فقط بدون أي نص إضافي."""
        
        return prompt
    
    def _parse_response(
        self,
        response_text: str,
        message: str,
        current_stage: ConversationStage
    ) -> IntentAnalysisResult:
        """تحليل استجابة الـ AI"""
        try:
            # Clean response
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            
            # Parse intent
            intent_str = data.get("intent", "unknown")
            try:
                intent = UserIntent(intent_str)
            except ValueError:
                intent = UserIntent.UNKNOWN
            
            # Parse next stage
            next_stage = None
            next_stage_str = data.get("next_stage")
            if next_stage_str:
                try:
                    next_stage = ConversationStage(next_stage_str)
                except ValueError:
                    pass
            
            # Clean extracted data (remove None values)
            extracted = data.get("extracted_data", {})
            extracted = {k: v for k, v in extracted.items() if v is not None and v != ""}
            
            # تحويل price إلى value
            if 'price' in extracted and 'value' not in extracted:
                extracted['value'] = extracted['price']
                del extracted['price']
            
            return IntentAnalysisResult(
                intent=intent,
                confidence=float(data.get("confidence", 0.5)),
                extracted_data=extracted,
                should_transition=data.get("should_transition", False),
                next_stage=next_stage,
                response_hint=data.get("response_hint", ""),
                raw_response=response_text
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return self._fallback_analysis(message, current_stage)
    
    def _fallback_analysis(
        self,
        message: str,
        current_stage: ConversationStage
    ) -> IntentAnalysisResult:
        """
        تحليل احتياطي بسيط - يستخدم فقط في حالة فشل الـ AI
        لا يوجد كلمات ثابتة - النظام يعتمد 100% على الـ AI
        """
        return IntentAnalysisResult(
            intent=UserIntent.UNKNOWN,
            confidence=0.3,
            extracted_data={},
            should_transition=False,
            next_stage=None,
            response_hint=""
        )


# Singleton instance
ai_intent_analyzer = AIIntentAnalyzer()
