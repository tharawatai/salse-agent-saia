"""
ModificationHandler - معالجة التعديل والرجوع والإلغاء
مع حفظ كل الأحداث في قاعدة البيانات
"""
import logging
from typing import Optional, Dict, Any

from ..ai_intent_analyzer import ConversationStage
from ..context_models import ConversationContext
from ..cache_manager import UserSession
from ..data_persistence_service import AsyncSessionPersistenceService
from .stage_validator import StageValidator

logger = logging.getLogger(__name__)


class ModificationHandler:
    """معالج طلبات التعديل والرجوع والإلغاء"""
    
    def __init__(self, cache_manager, responses_generator):
        """
        Args:
            cache_manager: مدير الكاش
            responses_generator: مولد الردود
        """
        self.cache_manager = cache_manager
        self.responses = responses_generator
    
    async def handle_modification_request(
        self,
        ai_result: Dict,
        context: ConversationContext,
        cached_session: UserSession = None
    ) -> Optional[Dict[str, Any]]:
        """
        معالجة طلبات التعديل والرجوع والإلغاء بناءً على تحليل AI
        
        Args:
            ai_result: نتيجة تحليل AI
            context: سياق المحادثة
            cached_session: جلسة الكاش
        
        Returns:
            Dict إذا تم معالجة الطلب، None إذا لم يكن طلب تعديل
        """
        modification_request = ai_result.get('modification_request', 'none')
        wants_to_restart = ai_result.get('wants_to_restart', False)
        field_to_edit = ai_result.get('field_to_edit', 'none')
        is_partial_correction = ai_result.get('is_partial_correction', False)
        
        if modification_request == 'none' and not wants_to_restart:
            return None
        
        current_stage = context.current_stage.value
        logger.info(f"🤖 AI detected modification: {modification_request}, restart={wants_to_restart}, field={field_to_edit}, partial={is_partial_correction} at stage {current_stage}")
        
        # إلغاء كامل / البدء من جديد
        if modification_request == 'cancel' or wants_to_restart:
            return await self._handle_cancel(context, cached_session, ai_result.get('ai_response'))
        
        # تعديل بيانات السيارة
        if modification_request == 'edit_vehicle':
            return await self._handle_edit_vehicle(
                context, cached_session, ai_result.get('ai_response'),
                field_to_edit=field_to_edit if field_to_edit != 'none' else None,
                is_partial=is_partial_correction
            )
        
        # 🆕 طلب سيارة جديدة (مسح البيانات القديمة)
        if modification_request == 'new_vehicle':
            return await self._handle_new_vehicle(context, cached_session, ai_result.get('ai_response'))
        
        # 🆕 استخدام البيانات المحفوظة
        if modification_request == 'use_saved_data':
            return await self._handle_use_saved_data(context, cached_session, ai_result.get('ai_response'))
        
        # تعديل البيانات الشخصية
        if modification_request == 'edit_profile':
            return await self._handle_edit_profile(
                context, cached_session, ai_result.get('ai_response'),
                field_to_edit=field_to_edit if field_to_edit != 'none' else None,
                is_partial=is_partial_correction
            )
        
        # تغيير العرض
        if modification_request == 'change_offer':
            return await self._handle_change_offer(context, cached_session, ai_result.get('ai_response'))
        
        # رجوع للخطوة السابقة
        if modification_request == 'go_back':
            return await self._handle_go_back(context, cached_session, ai_result.get('ai_response'))
        
        return None
    
    async def _handle_cancel(
        self,
        context: ConversationContext,
        cached_session: UserSession = None,
        ai_response: str = None
    ) -> Dict[str, Any]:
        """معالجة طلب الإلغاء"""
        
        old_stage = context.current_stage.value
        
        # حفظ البيانات قبل المسح
        data_before = {
            'vehicle_data': context.vehicle_data.copy() if context.vehicle_data else {},
            'profile_data': context.profile_data.copy() if context.profile_data else {},
            'selected_offer': context.selected_offer,
            'offers_count': len(context.offers_shown) if context.offers_shown else 0,
        }
        
        # مسح البيانات
        context.vehicle_data = {}
        context.profile_data = {}
        context.offers_shown = []
        context.selected_offer = None
        context.selected_offer_id = None
        context.order_id = None
        context.invoice_id = None
        context.policy_id = None
        
        # العودة للبداية
        context.current_stage = ConversationStage.GREETING
        
        # مسح الكاش
        if cached_session and self.cache_manager:
            self.cache_manager.clear_session(cached_session.session_id)
            
            # حفظ حدث الإلغاء في قاعدة البيانات
            await self._save_modification_event(
                session_id=cached_session.session_id,
                event_type='cancel',
                stage_at_event=old_stage,
                target_stage='greeting',
                data_before=data_before,
                data_after={},
                reason='طلب المستخدم إلغاء العملية',
                system_response=ai_response
            )
        
        logger.info(f"🚫 Session cancelled: {old_stage} → greeting")
        
        if ai_response:
            response = ai_response
        else:
            response = """تم إلغاء العملية بنجاح ✅

لا تقلق، يمكنك البدء من جديد في أي وقت!

مرحباً بك في SAIA للتأمين 🚗
كيف يمكنني مساعدتك اليوم؟

• تأمين شامل
• تأمين ضد الغير"""
        
        return {
            'success': True,
            'response_message': response,
            'next_stage': ConversationStage.GREETING,
            'data_collected': {'action': 'cancelled', 'previous_stage': old_stage}
        }
    
    async def _handle_edit_vehicle(
        self,
        context: ConversationContext,
        cached_session: UserSession = None,
        ai_response: str = None,
        field_to_edit: str = None,
        is_partial: bool = False
    ) -> Dict[str, Any]:
        """
        معالجة طلب تعديل بيانات السيارة
        يحتفظ بالبيانات الصحيحة ويطلب فقط تصحيح الحقل الخاطئ
        
        Args:
            context: سياق المحادثة
            cached_session: جلسة الكاش
            ai_response: رد AI
            field_to_edit: الحقل المحدد للتعديل (إذا وجد)
            is_partial: هل هو تعديل جزئي (حقل واحد فقط)
        """
        
        old_stage = context.current_stage.value
        old_vehicle = context.vehicle_data.copy()
        
        # حفظ البيانات قبل التعديل
        data_before = {
            'vehicle_data': old_vehicle,
            'offers_count': len(context.offers_shown) if context.offers_shown else 0,
            'selected_offer': context.selected_offer,
        }
        
        # أسماء الحقول بالعربية
        field_names = {
            'brand': 'الماركة',
            'model': 'الموديل',
            'year': 'سنة الصنع',
            'value': 'القيمة',
            'plate_no': 'رقم اللوحة'
        }
        
        # 🆕 تعديل جزئي - حقل واحد فقط
        if field_to_edit and field_to_edit in field_names:
            # مسح الحقل المحدد فقط
            if field_to_edit in context.vehicle_data:
                del context.vehicle_data[field_to_edit]
            
            field_name = field_names.get(field_to_edit, field_to_edit)
            
            # بناء رد يوضح البيانات المحفوظة
            response = f"""حسناً، سأحتفظ بالبيانات الصحيحة وأطلب منك تصحيح {field_name} فقط.

📋 البيانات المحفوظة:
"""
            if context.vehicle_data.get('brand'):
                response += f"• الماركة: {context.vehicle_data.get('brand')}\n"
            if context.vehicle_data.get('model'):
                response += f"• الموديل: {context.vehicle_data.get('model')}\n"
            if context.vehicle_data.get('year'):
                response += f"• السنة: {context.vehicle_data.get('year')}\n"
            if context.vehicle_data.get('value'):
                response += f"• القيمة: {context.vehicle_data.get('value'):,} ريال\n"
            if context.vehicle_data.get('plate_no'):
                response += f"• اللوحة: {context.vehicle_data.get('plate_no')}\n"
            
            response += f"\n✏️ يرجى إدخال {field_name} الصحيح/ة:"
            
            logger.info(f"✏️ Partial edit vehicle: field={field_to_edit}, kept data={context.vehicle_data}")
        
        elif is_partial and not field_to_edit:
            # المستخدم يريد تعديل جزئي لكن لم يحدد الحقل
            response = ai_response or """ما الحقل الذي تريد تعديله؟

البيانات الحالية:
"""
            if old_vehicle.get('brand'):
                response += f"• الماركة: {old_vehicle.get('brand')}\n"
            if old_vehicle.get('model'):
                response += f"• الموديل: {old_vehicle.get('model')}\n"
            if old_vehicle.get('year'):
                response += f"• السنة: {old_vehicle.get('year')}\n"
            if old_vehicle.get('value'):
                response += f"• القيمة: {old_vehicle.get('value'):,} ريال\n"
            if old_vehicle.get('plate_no'):
                response += f"• اللوحة: {old_vehicle.get('plate_no')}\n"
            
            response += "\nأخبرني أي حقل تريد تعديله (الماركة، الموديل، السنة، القيمة، اللوحة)."
            
            logger.info(f"✏️ Partial edit requested but no field specified")
        
        else:
            # تعديل كامل - مسح كل البيانات
            context.vehicle_data = {}
            
            response = ai_response or """تم إلغاء بيانات السيارة السابقة ✅

📝 أدخل بيانات سيارتك من جديد:

• الماركة (مثل: تويوتا، هوندا)
• الموديل (مثل: كامري، اكورد)
• سنة الصنع
• القيمة التقديرية
• رقم اللوحة"""
            
            logger.info(f"✏️ Full edit vehicle: cleared all data")
        
        # مسح العروض (ستتغير بتغير السيارة)
        context.offers_shown = []
        context.selected_offer = None
        context.selected_offer_id = None
        
        # العودة لمرحلة جمع بيانات السيارة
        context.current_stage = ConversationStage.COLLECTING_VEHICLE
        
        # تحديث الكاش
        if cached_session and self.cache_manager:
            # مسح العروض فقط
            self.cache_manager.clear_selected_offer(cached_session.session_id)
            
            # حفظ حدث التعديل في قاعدة البيانات
            await self._save_modification_event(
                session_id=cached_session.session_id,
                event_type='edit_vehicle',
                stage_at_event=old_stage,
                target_stage='collecting_vehicle',
                data_before=data_before,
                data_after={'vehicle_data': context.vehicle_data, 'field_edited': field_to_edit},
                reason=f'طلب المستخدم تعديل {"حقل " + field_names.get(field_to_edit, field_to_edit) if field_to_edit else "بيانات السيارة"}',
                system_response=response
            )
        
        logger.info(f"✏️ Edit vehicle: {old_stage} → collecting_vehicle (partial={is_partial}, field={field_to_edit})")
        
        return {
            'success': True,
            'response_message': response,
            'next_stage': ConversationStage.COLLECTING_VEHICLE,
            'data_collected': {
                'action': 'edit_vehicle',
                'previous_data': old_vehicle,
                'kept_data': context.vehicle_data,
                'field_edited': field_to_edit,
                'is_partial': is_partial
            }
        }
    
    async def _handle_edit_profile(
        self,
        context: ConversationContext,
        cached_session: UserSession = None,
        ai_response: str = None,
        field_to_edit: str = None,
        is_partial: bool = False
    ) -> Dict[str, Any]:
        """
        معالجة طلب تعديل البيانات الشخصية
        يحتفظ بالبيانات الصحيحة ويطلب فقط تصحيح الحقل الخاطئ
        
        Args:
            context: سياق المحادثة
            cached_session: جلسة الكاش
            ai_response: رد AI
            field_to_edit: الحقل المحدد للتعديل (إذا وجد)
            is_partial: هل هو تعديل جزئي (حقل واحد فقط)
        """
        
        old_stage = context.current_stage.value
        old_profile = context.profile_data.copy()
        
        # حفظ البيانات قبل المسح
        data_before = {
            'profile_data': old_profile,
        }
        
        # أسماء الحقول بالعربية
        field_names = {
            'national_id': 'رقم الهوية',
            'birth_date': 'تاريخ الميلاد'
        }
        
        # 🆕 تعديل جزئي - حقل واحد فقط
        if field_to_edit and field_to_edit in field_names:
            # مسح الحقل المحدد فقط
            if field_to_edit in context.profile_data:
                del context.profile_data[field_to_edit]
            
            field_name = field_names.get(field_to_edit, field_to_edit)
            
            # بناء رد يوضح البيانات المحفوظة
            response = f"""حسناً، سأحتفظ بالبيانات الصحيحة وأطلب منك تصحيح {field_name} فقط.

📋 البيانات المحفوظة:
"""
            if context.profile_data.get('national_id'):
                response += f"• رقم الهوية: {context.profile_data.get('national_id')}\n"
            if context.profile_data.get('birth_date'):
                response += f"• تاريخ الميلاد: {context.profile_data.get('birth_date')}\n"
            
            response += f"\n✏️ يرجى إدخال {field_name} الصحيح:"
            
            logger.info(f"✏️ Partial edit profile: field={field_to_edit}, kept data={context.profile_data}")
        
        elif is_partial and not field_to_edit:
            # المستخدم يريد تعديل جزئي لكن لم يحدد الحقل
            response = ai_response or """ما الحقل الذي تريد تعديله؟

البيانات الحالية:
"""
            if old_profile.get('national_id'):
                response += f"• رقم الهوية: {old_profile.get('national_id')}\n"
            if old_profile.get('birth_date'):
                response += f"• تاريخ الميلاد: {old_profile.get('birth_date')}\n"
            
            response += "\nأخبرني أي حقل تريد تعديله (رقم الهوية أو تاريخ الميلاد)."
            
            logger.info(f"✏️ Partial edit profile requested but no field specified")
        
        else:
            # تعديل كامل - مسح كل البيانات
            context.profile_data = {}
            
            response = ai_response or """تم إلغاء البيانات الشخصية السابقة ✅

📝 أدخل بياناتك الشخصية:

• رقم الهوية الوطنية (10 أرقام)
• تاريخ الميلاد (مثل: 1990-01-15)"""
            
            logger.info(f"✏️ Full edit profile: cleared all data")
        
        # العودة لمرحلة جمع البيانات الشخصية
        context.current_stage = ConversationStage.COLLECTING_PROFILE
        
        # تحديث الكاش
        if cached_session and self.cache_manager:
            if not is_partial and not field_to_edit:
                self.cache_manager.clear_profile_data(cached_session.session_id)
            
            # حفظ حدث التعديل في قاعدة البيانات
            await self._save_modification_event(
                session_id=cached_session.session_id,
                event_type='edit_profile',
                stage_at_event=old_stage,
                target_stage='collecting_profile',
                data_before=data_before,
                data_after={'profile_data': context.profile_data, 'field_edited': field_to_edit},
                reason=f'طلب المستخدم تعديل {"حقل " + field_names.get(field_to_edit, field_to_edit) if field_to_edit else "البيانات الشخصية"}',
                system_response=response
            )
        
        logger.info(f"✏️ Edit profile: {old_stage} → collecting_profile (partial={is_partial}, field={field_to_edit})")
        
        return {
            'success': True,
            'response_message': response,
            'next_stage': ConversationStage.COLLECTING_PROFILE,
            'data_collected': {
                'action': 'edit_profile',
                'previous_data': old_profile,
                'kept_data': context.profile_data,
                'field_edited': field_to_edit,
                'is_partial': is_partial
            }
        }
    
    async def _handle_change_offer(
        self,
        context: ConversationContext,
        cached_session: UserSession = None,
        ai_response: str = None
    ) -> Dict[str, Any]:
        """معالجة طلب تغيير العرض - إعادة عرض قائمة العروض"""
        
        old_stage = context.current_stage.value
        old_offer = context.selected_offer
        
        # حفظ البيانات قبل المسح
        data_before = {
            'selected_offer': old_offer,
            'selected_offer_id': context.selected_offer_id,
        }
        
        # مسح العرض المختار
        context.selected_offer = None
        context.selected_offer_id = None
        
        # العودة لمرحلة عرض العروض
        context.current_stage = ConversationStage.SHOWING_OFFERS
        
        # تحديث الكاش
        if cached_session and self.cache_manager:
            self.cache_manager.clear_selected_offer(cached_session.session_id)
            
            # حفظ حدث التعديل في قاعدة البيانات
            await self._save_modification_event(
                session_id=cached_session.session_id,
                event_type='change_offer',
                stage_at_event=old_stage,
                target_stage='showing_offers',
                data_before=data_before,
                data_after={},
                reason='طلب المستخدم تغيير العرض',
                system_response=ai_response
            )
        
        logger.info(f"🔄 Change offer: {old_stage} → showing_offers")
        
        # 🆕 إعادة عرض قائمة العروض
        from ..responses.message_formatter import MessageFormatter
        
        if context.offers_shown:
            response = MessageFormatter.format_offers_list(context.offers_shown)
        else:
            response = "تم إلغاء العرض المختار ✅\n\nاختر عرضاً آخر من القائمة."
        
        return {
            'success': True,
            'response_message': response,
            'next_stage': ConversationStage.SHOWING_OFFERS,
            'data_collected': {'action': 'change_offer', 'previous_offer': old_offer},
            'show_offers': True  # علامة لإعادة عرض العروض
        }
    
    async def _handle_new_vehicle(
        self,
        context: ConversationContext,
        cached_session: UserSession = None,
        ai_response: str = None
    ) -> Dict[str, Any]:
        """
        معالجة طلب تأمين لسيارة جديدة
        مسح كل بيانات السيارة القديمة والعروض والبدء من جديد
        """
        
        old_stage = context.current_stage.value
        
        # حفظ البيانات قبل المسح
        data_before = {
            'vehicle_data': context.vehicle_data.copy() if context.vehicle_data else {},
            'offers_count': len(context.offers_shown) if context.offers_shown else 0,
            'selected_offer': context.selected_offer,
        }
        
        # مسح بيانات السيارة والعروض
        context.vehicle_data = {}
        context.offers_shown = []
        context.selected_offer = None
        context.selected_offer_id = None
        
        # العودة لمرحلة جمع بيانات السيارة
        context.current_stage = ConversationStage.COLLECTING_VEHICLE
        
        # تحديث الكاش
        if cached_session and self.cache_manager:
            self.cache_manager.clear_vehicle_data(cached_session.session_id)
            self.cache_manager.clear_selected_offer(cached_session.session_id)
            
            # حفظ حدث التعديل في قاعدة البيانات
            await self._save_modification_event(
                session_id=cached_session.session_id,
                event_type='new_vehicle',
                stage_at_event=old_stage,
                target_stage='collecting_vehicle',
                data_before=data_before,
                data_after={},
                reason='طلب المستخدم تأمين لسيارة جديدة',
                system_response=ai_response
            )
        
        logger.info(f"🚗 New vehicle request: {old_stage} → collecting_vehicle (cleared old data)")
        
        response = ai_response or """تمام! 🚗

📝 أدخل بيانات سيارتك الجديدة:

• الماركة (مثل: تويوتا، هوندا)
• الموديل (مثل: كامري، اكورد)
• سنة الصنع
• القيمة التقديرية
• رقم اللوحة

يمكنك إرسالها في رسالة واحدة."""
        
        return {
            'success': True,
            'response_message': response,
            'next_stage': ConversationStage.COLLECTING_VEHICLE,
            'data_collected': {
                'action': 'new_vehicle',
                'previous_vehicle': data_before.get('vehicle_data', {})
            }
        }
    
    async def _handle_use_saved_data(
        self,
        context: ConversationContext,
        cached_session: UserSession = None,
        ai_response: str = None
    ) -> Dict[str, Any]:
        """
        معالجة طلب استخدام البيانات المحفوظة من جلسات سابقة
        """
        
        old_stage = context.current_stage.value
        
        # التحقق من وجود بيانات محفوظة
        has_saved_vehicle = hasattr(context, '_saved_vehicle') and context._saved_vehicle
        has_saved_profile = hasattr(context, '_saved_profile') and context._saved_profile
        
        if not has_saved_vehicle and not has_saved_profile:
            # لا توجد بيانات محفوظة
            response = """عذراً، لا توجد بيانات محفوظة سابقة لك.

📝 يرجى إدخال بيانات سيارتك:
• الماركة والموديل
• سنة الصنع
• القيمة التقديرية
• رقم اللوحة"""
            
            return {
                'success': True,
                'response_message': response,
                'next_stage': context.current_stage,
                'data_collected': {'action': 'use_saved_data', 'found': False}
            }
        
        # استعادة البيانات المحفوظة
        restored_data = {}
        
        if has_saved_vehicle:
            context.vehicle_data = context._saved_vehicle.copy()
            restored_data['vehicle'] = context.vehicle_data
            logger.info(f"📦 Restored saved vehicle data: {context.vehicle_data}")
        
        if has_saved_profile:
            context.profile_data = context._saved_profile.copy()
            restored_data['profile'] = context.profile_data
            logger.info(f"📦 Restored saved profile data: {context.profile_data}")
        
        # بناء رد يعرض البيانات المستعادة
        response_parts = ["✅ تم استعادة بياناتك المحفوظة!\n"]
        
        if has_saved_vehicle:
            v = context.vehicle_data
            response_parts.append("🚗 *بيانات السيارة:*")
            if v.get('brand'): response_parts.append(f"• الماركة: {v['brand']}")
            if v.get('model'): response_parts.append(f"• الموديل: {v['model']}")
            if v.get('year'): response_parts.append(f"• السنة: {v['year']}")
            if v.get('value'): response_parts.append(f"• القيمة: {v['value']:,} ريال")
            if v.get('plate_no'): response_parts.append(f"• اللوحة: {v['plate_no']}")
            response_parts.append("")
        
        if has_saved_profile:
            p = context.profile_data
            response_parts.append("👤 *البيانات الشخصية:*")
            if p.get('national_id'): response_parts.append(f"• الهوية: {p['national_id']}")
            if p.get('birth_date'): response_parts.append(f"• الميلاد: {p['birth_date']}")
            response_parts.append("")
        
        response_parts.append("هل تريد استخدام هذه البيانات؟")
        
        response = "\n".join(response_parts)
        
        # تحديد المرحلة التالية
        if has_saved_vehicle and context.vehicle_data:
            context.current_stage = ConversationStage.CONFIRMING_VEHICLE
            next_stage = ConversationStage.CONFIRMING_VEHICLE
        else:
            next_stage = context.current_stage
        
        # حفظ حدث الاستعادة
        if cached_session and self.cache_manager:
            await self._save_modification_event(
                session_id=cached_session.session_id,
                event_type='use_saved_data',
                stage_at_event=old_stage,
                target_stage=next_stage.value,
                data_before={},
                data_after=restored_data,
                reason='طلب المستخدم استخدام البيانات المحفوظة',
                system_response=response
            )
        
        logger.info(f"📦 Used saved data: {old_stage} → {next_stage.value}")
        
        return {
            'success': True,
            'response_message': response,
            'next_stage': next_stage,
            'data_collected': {
                'action': 'use_saved_data',
                'found': True,
                'restored': restored_data
            }
        }
    
    async def _handle_go_back(
        self,
        context: ConversationContext,
        cached_session: UserSession = None,
        ai_response: str = None
    ) -> Dict[str, Any]:
        """معالجة طلب الرجوع للخطوة السابقة"""
        
        current_stage = context.current_stage.value
        previous_stage = StageValidator.get_previous_stage(current_stage)
        
        # تحديث المرحلة
        try:
            context.current_stage = ConversationStage(previous_stage)
        except ValueError:
            context.current_stage = ConversationStage.GREETING
            previous_stage = 'greeting'
        
        # حفظ حدث الرجوع في قاعدة البيانات
        if cached_session and self.cache_manager:
            await self._save_modification_event(
                session_id=cached_session.session_id,
                event_type='go_back',
                stage_at_event=current_stage,
                target_stage=previous_stage,
                data_before={'current_stage': current_stage},
                data_after={'current_stage': previous_stage},
                reason='طلب المستخدم الرجوع للخطوة السابقة',
                system_response=ai_response
            )
        
        logger.info(f"⬅️ Go back: {current_stage} → {previous_stage}")
        
        if ai_response:
            response = ai_response
        else:
            response = self._get_stage_prompt(previous_stage, context)
        
        return {
            'success': True,
            'response_message': response,
            'next_stage': context.current_stage,
            'data_collected': {'action': 'go_back', 'from_stage': current_stage, 'to_stage': previous_stage}
        }
    
    async def _save_modification_event(
        self,
        session_id: str,
        event_type: str,
        stage_at_event: str,
        target_stage: str,
        data_before: Dict = None,
        data_after: Dict = None,
        reason: str = None,
        trigger_message: str = None,
        system_response: str = None
    ):
        """حفظ حدث التعديل في قاعدة البيانات"""
        try:
            await AsyncSessionPersistenceService.save_modification_event(
                session_id=session_id,
                event_type=event_type,
                stage_at_event=stage_at_event,
                target_stage=target_stage,
                data_before=data_before or {},
                data_after=data_after or {},
                reason=reason,
                trigger_message=trigger_message,
                system_response=system_response,
                is_successful=True
            )
            logger.info(f"💾 Saved modification event: {event_type}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save modification event: {e}")
    
    def _get_stage_prompt(self, stage: str, context: ConversationContext) -> str:
        """توليد رسالة مناسبة للمرحلة"""
        
        prompts = {
            'greeting': """مرحباً بك في SAIA للتأمين 🚗

كيف يمكنني مساعدتك اليوم؟
• تأمين شامل
• تأمين ضد الغير""",
            
            'service_details': """ما نوع التأمين الذي تريده؟

• تأمين شامل - تغطية كاملة للسيارة
• تأمين ضد الغير - تغطية الطرف الثالث فقط""",
            
            'collecting_vehicle': """📝 أدخل بيانات سيارتك:

• الماركة (مثل: تويوتا، هوندا)
• الموديل (مثل: كامري، اكورد)
• سنة الصنع
• القيمة التقديرية
• رقم اللوحة""",
            
            'confirming_vehicle': f"""📋 بيانات سيارتك:

🚗 الماركة: {context.vehicle_data.get('brand', '-')}
📱 الموديل: {context.vehicle_data.get('model', '-')}
📅 السنة: {context.vehicle_data.get('year', '-')}
💰 القيمة: {context.vehicle_data.get('value', '-')} ريال
🔢 اللوحة: {context.vehicle_data.get('plate_no', '-')}

هل البيانات صحيحة؟""",
            
            'showing_offers': "جاري جلب العروض المتاحة...",
            
            'offer_details': "اختر رقم العرض لعرض التفاصيل",
            
            'collecting_profile': """📝 أدخل بياناتك الشخصية:

• رقم الهوية الوطنية (10 أرقام)
• تاريخ الميلاد (مثل: 1990-01-15)""",
            
            'confirming_profile': f"""📋 بياناتك الشخصية:

🆔 الهوية: {context.profile_data.get('national_id', '-')}
📅 الميلاد: {context.profile_data.get('birth_date', '-')}

هل البيانات صحيحة؟""",
            
            'order_summary': "جاري تجهيز ملخص الطلب...",
            
            'confirmation': "هل تريد تأكيد الطلب والمتابعة للدفع؟",
            
            'payment_pending': "جاري تجهيز الفاتورة...",
            
            'completed': "تم إكمال العملية بنجاح! 🎉"
        }
        
        return prompts.get(stage, "كيف يمكنني مساعدتك؟")
