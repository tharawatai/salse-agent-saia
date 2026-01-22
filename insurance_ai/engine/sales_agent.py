"""
ProfessionalInsuranceEngineV2 - المحرك الرئيسي
100% AI Driven - يعتمد على Gemini Structured Output
"""
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal

from asgiref.sync import sync_to_async

from insurance_core.models import User
from ..ai_intent_analyzer import ConversationStage
from ..context_models import ConversationContext
from ..cache_manager import (
    get_cache_manager, UserSession, get_insurance_cache
)

from ..ai import SmartGeminiEngine
from ..context import SessionManager, StageResult, get_context_store
from ..extraction import DataExtractor
from ..database import OffersRepository, OrdersRepository, PolicyRepository
from ..responses import OffersResponses, ProfileResponses, PolicyResponses, ServicesResponses
from .stage_validator import StageValidator, VALID_STAGES, VALID_TRANSITIONS
from .modification_handler import ModificationHandler

logger = logging.getLogger(__name__)


class ProfessionalInsuranceEngineV2:
    """المحرك الاحترافي - 100% AI Driven"""
    
    # خريطة المراحل التالية
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
    
    def __init__(self):
        self.gemini = SmartGeminiEngine()
        self.session_manager = SessionManager()
        self.cache_manager = get_cache_manager()
        self.modification_handler = ModificationHandler(self.cache_manager, None)
        logger.info("🚀 ProfessionalInsuranceEngineV2 - Full AI Mode with Cache Manager")
    
    async def process_message(
        self,
        conversation_id: str,
        message: str,
        user: User = None,
        phone: str = None
    ) -> StageResult:
        """
        معالجة رسالة العميل
        
        Args:
            conversation_id: معرف المحادثة
            message: الرسالة
            user: المستخدم
            phone: رقم الهاتف
        
        Returns:
            StageResult: نتيجة المعالجة
        """
        
        logger.info(f"📨 Processing: '{message}' | conv={conversation_id}")
        
        # استخدام Cache Manager للجلسات
        user_identifier = phone or conversation_id
        cached_session = self.cache_manager.get_or_create_session(user_identifier)
        
        # تحديث عداد الرسائل
        self.cache_manager.increment_message_count(cached_session.session_id, message)
        
        # الحصول على السياق
        context = await self.session_manager.get_or_create_context(
            conversation_id=conversation_id,
            phone=phone,
            user=user
        )
        
        # مزامنة البيانات من الكاش إلى السياق
        self._sync_cache_to_context(cached_session, context)
        
        current_stage = context.current_stage.value
        logger.info(f"📍 Stage: {current_stage} | Session: {cached_session.session_id[:8]}...")
        
        # تجهيز البيانات للـ AI
        context_data = {
            'vehicle': context.vehicle_data,
            'profile': context.profile_data,
            'selected_offer': context.selected_offer
        }
        
        # جلب العروض إذا لزم الأمر
        offers_list = None
        if current_stage == 'showing_offers':
            offers_list = context.offers_shown
        
        # استدعاء الذكاء الاصطناعي
        ai_result = await self.gemini.process_with_ai(
            message=message,
            current_stage=current_stage,
            context_data=context_data,
            available_offers=offers_list
        )
        
        # تحديث البيانات المستخرجة
        DataExtractor.update_from_ai_result(context, ai_result, message)
        
        # تحديث الكاش بالبيانات الجديدة
        self._sync_context_to_cache(context, cached_session)
        
        # معالجة الانتقال والإجراءات الخاصة
        result = await self._handle_stage_logic(context, ai_result, message, cached_session)
        
        # حفظ السياق
        await self.session_manager.save_context(context)
        
        return result
    
    def _sync_cache_to_context(self, cached_session: UserSession, context: ConversationContext):
        """مزامنة البيانات من الكاش إلى السياق"""
        fresh_session = self.cache_manager.get_session(cached_session.session_id)
        if fresh_session:
            cached_session = fresh_session
        
        # نقل بيانات السيارة
        if cached_session.vehicle:
            v = cached_session.vehicle
            if v.brand: context.vehicle_data['brand'] = v.brand
            if v.model: context.vehicle_data['model'] = v.model
            if v.year: context.vehicle_data['year'] = v.year
            if v.value: context.vehicle_data['value'] = v.value
            if v.plate_no: context.vehicle_data['plate_no'] = v.plate_no
            if v.service_type: context.vehicle_data['service_type'] = v.service_type
        
        # نقل بيانات العميل
        if cached_session.profile:
            p = cached_session.profile
            if p.national_id: context.profile_data['national_id'] = p.national_id
            if p.birth_date: context.profile_data['birth_date'] = p.birth_date
            if p.phone: context.profile_data['phone'] = p.phone
        
        # نقل العروض
        if cached_session.available_offers:
            context.offers_shown = cached_session.available_offers
            logger.debug(f"📦 Synced {len(cached_session.available_offers)} offers from cache to context")
        if cached_session.selected_offer:
            context.selected_offer = cached_session.selected_offer
            context.selected_offer_id = cached_session.selected_offer_id
            logger.debug(f"📦 Synced selected offer {cached_session.selected_offer_id} from cache to context")
    
    def _sync_context_to_cache(self, context: ConversationContext, cached_session: UserSession):
        """مزامنة البيانات من السياق إلى الكاش"""
        
        def clean_value(val):
            if val is None:
                return None
            if isinstance(val, str) and val.lower() in ['null', 'none', '']:
                return None
            return val
        
        # تحديث بيانات السيارة
        v = context.vehicle_data
        vehicle_updates = {
            'brand': clean_value(v.get('brand')),
            'model': clean_value(v.get('model')),
            'year': clean_value(v.get('year')),
            'value': clean_value(v.get('value')),
            'plate_no': clean_value(v.get('plate_no')),
            'service_type': clean_value(v.get('service_type'))
        }
        vehicle_updates = {k: v for k, v in vehicle_updates.items() if v is not None}
        
        if vehicle_updates:
            self.cache_manager.update_vehicle_data(cached_session.session_id, **vehicle_updates)
        
        # تحديث بيانات العميل
        p = context.profile_data
        profile_updates = {
            'national_id': clean_value(p.get('national_id')),
            'birth_date': clean_value(p.get('birth_date')),
            'phone': clean_value(context.phone)
        }
        profile_updates = {k: v for k, v in profile_updates.items() if v is not None}
        
        if profile_updates:
            self.cache_manager.update_profile_data(cached_session.session_id, **profile_updates)
        
        # تحديث المرحلة
        self.cache_manager.update_stage(cached_session.session_id, context.current_stage.value)
        
        # التحقق من اكتمال البيانات
        progress = self.cache_manager.get_session_progress(cached_session.session_id)
        if progress:
            logger.debug(f"📊 Session progress: vehicle={progress.get('vehicle_complete')}, profile={progress.get('profile_complete')}")
    
    async def _handle_stage_logic(
        self,
        context: ConversationContext,
        ai_result: Dict,
        message: str,
        cached_session: UserSession = None
    ) -> StageResult:
        """معالجة منطق المرحلة"""
        
        current_stage = context.current_stage.value
        should_transition = ai_result.get('should_move_to_next_stage', False)
        is_positive = ai_result.get('is_positive_response', False)
        ai_response = ai_result.get('ai_response', '')
        recommended_next = ai_result.get('recommended_next_stage', self.STAGE_FLOW.get(current_stage, current_stage))
        is_data_complete = ai_result.get('is_data_complete', False)
        
        logger.info(f"🔍 Stage Logic: current={current_stage}, should_transition={should_transition}, is_positive={is_positive}, recommended={recommended_next}")
        
        # معالجة التعديل والرجوع والإلغاء
        modification_result = await self.modification_handler.handle_modification_request(ai_result, context, cached_session)
        if modification_result:
            return StageResult(
                success=modification_result['success'],
                response_message=modification_result['response_message'],
                next_stage=modification_result['next_stage'],
                data_collected=modification_result.get('data_collected', {})
            )
        
        # الانتقال التلقائي الذكي للمراحل المبكرة
        result = await self._handle_auto_transitions(context, ai_result, cached_session)
        if result:
            return result
        
        # التحقق المحلي قبل الانتقال
        if should_transition and recommended_next != current_stage:
            is_valid, error_msg = StageValidator.validate_transition(current_stage, recommended_next, context)
            if not is_valid:
                logger.warning(f"⚠️ Transition blocked: {error_msg}")
                should_transition = False
                status = StageValidator.get_completion_status(current_stage, context)
                if status['missing_fields']:
                    ai_response += f"\n\n⚠️ البيانات الناقصة: {', '.join(status['missing_fields'])}"
        
        # معالجة خاصة لبعض المراحل
        result = await self._handle_special_stages(context, ai_result, cached_session, should_transition, is_positive)
        if result:
            return result
        
        # الرد الافتراضي
        return StageResult(
            success=True,
            response_message=ai_response,
            next_stage=context.current_stage,
            data_collected={}
        )
    
    async def _handle_auto_transitions(
        self,
        context: ConversationContext,
        ai_result: Dict,
        cached_session: UserSession
    ) -> Optional[StageResult]:
        """معالجة الانتقالات التلقائية"""
        
        current_stage = context.current_stage.value
        should_transition = ai_result.get('should_move_to_next_stage', False)
        
        # مرحلة الترحيب
        if current_stage == 'greeting':
            service_type = ai_result.get('extracted_service_type') or context.vehicle_data.get('service_type')
            if service_type:
                context.vehicle_data['service_type'] = service_type
                context.current_stage = ConversationStage.COLLECTING_VEHICLE
                logger.info(f"✅ Auto-transition: greeting → collecting_vehicle (service: {service_type})")
            elif should_transition:
                context.current_stage = ConversationStage.SERVICE_DETAILS
                logger.info(f"✅ Auto-transition: greeting → service_details")
        
        # مرحلة تفاصيل الخدمة
        if current_stage == 'service_details':
            service_type = ai_result.get('extracted_service_type') or context.vehicle_data.get('service_type')
            if service_type:
                context.vehicle_data['service_type'] = service_type
            
            has_vehicle_data = any([
                context.vehicle_data.get('brand'),
                context.vehicle_data.get('model'),
                context.vehicle_data.get('year'),
                context.vehicle_data.get('value'),
                context.vehicle_data.get('plate_no')
            ])
            
            if DataExtractor.is_vehicle_data_complete(context):
                context.current_stage = ConversationStage.CONFIRMING_VEHICLE
                logger.info(f"✅ Auto-transition: service_details → confirming_vehicle (vehicle data complete)")
            elif has_vehicle_data or service_type or should_transition:
                context.current_stage = ConversationStage.COLLECTING_VEHICLE
                logger.info(f"✅ Auto-transition: service_details → collecting_vehicle")
        
        # مرحلة جمع بيانات السيارة
        if current_stage == 'collecting_vehicle':
            if DataExtractor.is_vehicle_data_complete(context):
                context.current_stage = ConversationStage.CONFIRMING_VEHICLE
                confirm_response = await ProfileResponses.generate_vehicle_confirmation(context)
                logger.info(f"✅ Auto-transition: collecting_vehicle → confirming_vehicle")
                
                return StageResult(
                    success=True,
                    response_message=confirm_response,
                    next_stage=ConversationStage.CONFIRMING_VEHICLE,
                    data_collected={'vehicle': context.vehicle_data}
                )
            else:
                # AI يعرض حالة البيانات بنفسه الآن
                ai_response = ai_result.get('ai_response', '')
                
                return StageResult(
                    success=True,
                    response_message=ai_response,
                    next_stage=ConversationStage.COLLECTING_VEHICLE,
                    data_collected={'vehicle_partial': context.vehicle_data}
                )
        
        return None
    
    async def _handle_special_stages(
        self,
        context: ConversationContext,
        ai_result: Dict,
        cached_session: UserSession,
        should_transition: bool,
        is_positive: bool
    ) -> Optional[StageResult]:
        """معالجة المراحل الخاصة"""
        
        current_stage = context.current_stage.value
        
        # مرحلة تأكيد السيارة → جلب العروض
        if current_stage == 'confirming_vehicle' and should_transition and is_positive:
            offers = await OffersRepository.fetch_offers(
                service_type=context.vehicle_data.get('service_type', 'comprehensive'),
                vehicle_year=context.vehicle_data.get('year'),
                vehicle_value=Decimal(str(context.vehicle_data.get('value', 0))) if context.vehicle_data.get('value') else None
            )
            if offers:
                context.offers_shown = offers
                context.current_stage = ConversationStage.SHOWING_OFFERS
                
                if cached_session:
                    self.cache_manager.set_available_offers(cached_session.session_id, offers)
                
                offers_response = await OffersResponses.generate_offers_list(offers)
                logger.info(f"✅ Auto-transition: confirming_vehicle → showing_offers (عرض {len(offers)} عروض)")
                
                return StageResult(
                    success=True,
                    response_message=offers_response,
                    next_stage=ConversationStage.SHOWING_OFFERS,
                    data_collected={'offers_count': len(offers)}
                )
        
        # مرحلة عرض العروض → اختيار عرض
        if current_stage == 'showing_offers':
            selected_num = ai_result.get('selected_offer_number')
            logger.info(f"🔍 Showing offers: selected_num={selected_num}, offers_count={len(context.offers_shown)}")
            
            # استعادة العروض من الكاش إذا لم تكن موجودة
            if not context.offers_shown and cached_session:
                session = self.cache_manager.get_session(cached_session.session_id)
                if session and session.available_offers:
                    context.offers_shown = session.available_offers
                    logger.info(f"📦 Restored {len(context.offers_shown)} offers from cache")
            
            if selected_num and context.offers_shown and 1 <= selected_num <= len(context.offers_shown):
                offer = context.offers_shown[selected_num - 1]
                context.selected_offer = offer
                context.selected_offer_id = offer.get('id')
                
                if cached_session:
                    self.cache_manager.set_selected_offer(cached_session.session_id, offer)
                
                context.current_stage = ConversationStage.OFFER_DETAILS
                details_response = await OffersResponses.generate_offer_details(offer, selected_num)
                logger.info(f"✅ Auto-transition: showing_offers → offer_details (اختيار عرض {selected_num})")
                
                return StageResult(
                    success=True,
                    response_message=details_response,
                    next_stage=ConversationStage.OFFER_DETAILS,
                    data_collected={'selected_offer': offer}
                )
            
            # 🆕 إذا لم يتم اختيار عرض، عرض القائمة مرة أخرى
            elif context.offers_shown:
                # إذا طلب تفاصيل بدون تحديد رقم
                ai_response = ai_result.get('ai_response', '')
                if 'تفاصيل' in ai_response.lower() or not selected_num:
                    offers_response = await OffersResponses.generate_offers_list(context.offers_shown)
                    return StageResult(
                        success=True,
                        response_message=offers_response,
                        next_stage=ConversationStage.SHOWING_OFFERS,
                        data_collected={'offers_count': len(context.offers_shown)}
                    )
        
        # مرحلة تفاصيل العرض → جمع بيانات العميل
        if current_stage == 'offer_details':
            if not context.selected_offer_id and cached_session:
                session = self.cache_manager.get_session(cached_session.session_id)
                if session and session.selected_offer:
                    context.selected_offer = session.selected_offer
                    context.selected_offer_id = session.selected_offer_id
                    logger.info(f"📦 Restored selected offer from cache: {context.selected_offer_id}")
            
            if should_transition and is_positive and context.selected_offer_id:
                context.current_stage = ConversationStage.COLLECTING_PROFILE
                profile_request = await ProfileResponses.generate_profile_request()
                logger.info(f"✅ Auto-transition: offer_details → collecting_profile")
                
                return StageResult(
                    success=True,
                    response_message=profile_request,
                    next_stage=ConversationStage.COLLECTING_PROFILE,
                    data_collected={'offer_confirmed': True}
                )
        
        # مرحلة جمع بيانات العميل → تأكيد البيانات
        if current_stage == 'collecting_profile':
            if DataExtractor.is_profile_data_complete(context):
                context.current_stage = ConversationStage.CONFIRMING_PROFILE
                confirm_response = await ProfileResponses.generate_profile_confirmation(context)
                logger.info(f"✅ Auto-transition: collecting_profile → confirming_profile")
                
                return StageResult(
                    success=True,
                    response_message=confirm_response,
                    next_stage=ConversationStage.CONFIRMING_PROFILE,
                    data_collected={'profile': context.profile_data}
                )
            else:
                # AI يعرض حالة البيانات بنفسه الآن
                ai_response = ai_result.get('ai_response', '')
                
                return StageResult(
                    success=True,
                    response_message=ai_response,
                    next_stage=ConversationStage.COLLECTING_PROFILE,
                    data_collected={'profile_partial': context.profile_data}
                )
        
        # مرحلة تأكيد بيانات العميل → ملخص الطلب
        if current_stage == 'confirming_profile' and should_transition and is_positive:
            if context.profile_data.get('national_id') and context.profile_data.get('birth_date'):
                context.current_stage = ConversationStage.ORDER_SUMMARY
                
                if cached_session:
                    self.cache_manager.update_profile_data(cached_session.session_id, confirmed=True)
                
                summary_response = await ProfileResponses.generate_order_summary(context)
                logger.info(f"✅ Auto-transition: confirming_profile → order_summary")
                
                return StageResult(
                    success=True,
                    response_message=summary_response,
                    next_stage=ConversationStage.ORDER_SUMMARY,
                    data_collected={'profile_confirmed': True}
                )
        
        # مرحلة ملخص الطلب → إنشاء الطلب
        if current_stage == 'order_summary' and should_transition and is_positive:
            if context.selected_offer_id and context.vehicle_data and context.profile_data:
                context.current_stage = ConversationStage.CONFIRMATION
                
                result = await OrdersRepository.create_order_and_invoice(context)
                if result['success']:
                    context.order_id = result['order_id']
                    context.invoice_id = result['invoice_id']
                    context.current_stage = ConversationStage.PAYMENT_PENDING
                    
                    if cached_session:
                        session = self.cache_manager.get_session(cached_session.session_id)
                        if session:
                            session.order_id = result['order_id']
                            session.order_code = result['order_code']
                            session.invoice_id = result['invoice_id']
                            session.invoice_no = result['invoice_no']
                            self.cache_manager.update_session(session)
                    
                    # 🆕 توليد PDF للفاتورة
                    pdf_url = None
                    pdf_path = None
                    try:
                        from ..pdf_generator import pdf_generator
                        from django.conf import settings as django_settings
                        
                        # تحضير بيانات الفاتورة
                        invoice_data = {
                            'invoice_id': result.get('invoice_no', result.get('invoice_id')),
                            'order_code': result.get('order_code'),
                            'national_id': context.profile_data.get('national_id', ''),
                            'birth_date': context.profile_data.get('birth_date', ''),
                            'phone': context.phone,
                            'vehicle_brand': context.vehicle_data.get('brand', ''),
                            'vehicle_model': context.vehicle_data.get('model', ''),
                            'vehicle_year': context.vehicle_data.get('year', ''),
                            'plate_no': context.vehicle_data.get('plate_no', ''),
                            'vehicle_value': context.vehicle_data.get('value', 0),
                            'coverage_type': context.selected_offer.get('coverage_type', 'شامل') if context.selected_offer else 'شامل',
                            'company_name': context.selected_offer.get('company', '') if context.selected_offer else '',
                            'total_amount': result.get('amount', 0),
                        }
                        
                        # توليد PDF
                        pdf_path = pdf_generator.save_invoice_html(invoice_data)
                        
                        # بناء رابط كامل
                        base_url = getattr(django_settings, 'BASE_URL', 'http://127.0.0.1:8000')
                        pdf_url = f"{base_url}/api/ai/invoices/{result['invoice_id']}/pdf/"
                        
                        logger.info(f"📄 Invoice PDF generated: {pdf_path}")
                        
                        # 🆕 إرسال PDF عبر واتساب إذا كان هناك رقم هاتف
                        if context.phone and pdf_path:
                            try:
                                from whatsapp_integration.webhook import send_invoice_pdf_to_whatsapp
                                await send_invoice_pdf_to_whatsapp(
                                    phone_number=context.phone,
                                    pdf_path=pdf_path,
                                    invoice_no=result.get('invoice_no', str(result['invoice_id']))
                                )
                                logger.info(f"📤 Invoice PDF sent to WhatsApp: {context.phone}")
                            except Exception as wa_err:
                                logger.warning(f"⚠️ Could not send PDF to WhatsApp: {wa_err}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to generate invoice PDF: {e}")
                    
                    order_response = await PolicyResponses.generate_order_created(result)
                    
                    # إضافة رابط PDF للرد
                    if pdf_url:
                        order_response += f"\n\n📄 *رابط تحميل الفاتورة:*\n{pdf_url}"
                    
                    logger.info(f"✅ Auto-transition: order_summary → payment_pending (طلب {result['order_code']})")
                    
                    return StageResult(
                        success=True,
                        response_message=order_response,
                        next_stage=ConversationStage.PAYMENT_PENDING,
                        has_invoice=True,
                        invoice_url=pdf_url or f"/api/ai/invoices/{result['invoice_id']}/pdf/",
                        invoice_pdf_path=pdf_path,
                        data_collected=result
                    )
        
        # مرحلة انتظار الدفع → إصدار الوثيقة
        if current_stage == 'payment_pending' and should_transition and is_positive:
            result = await PolicyRepository.create_policy(context)
            if result['success']:
                context.policy_id = result['policy_id']
                context.current_stage = ConversationStage.COMPLETED
                
                if cached_session:
                    session = self.cache_manager.get_session(cached_session.session_id)
                    if session:
                        session.policy_id = result['policy_id']
                        session.policy_no = result['policy_no']
                        session.mark_completed()
                        self.cache_manager.update_session(session)
                
                policy_response = await PolicyResponses.generate_policy_issued(result)
                logger.info(f"✅ Auto-transition: payment_pending → completed (وثيقة {result['policy_no']})")
                
                return StageResult(
                    success=True,
                    response_message=policy_response,
                    next_stage=ConversationStage.COMPLETED,
                    has_policy=True,
                    policy_url=result.get('pdf_url'),
                    data_collected=result
                )
        
        return None
