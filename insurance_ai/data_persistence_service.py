"""
SAIA Insurance - Data Persistence Service
خدمة حفظ البيانات في قاعدة البيانات

المميزات:
- حفظ تلقائي عند كل تحديث (ليس فقط عند الاكتمال)
- تتبع كل الرسائل والانتقالات
- دعم async و sync
- تكامل مع cache_manager
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class SessionPersistenceService:
    """
    خدمة حفظ بيانات الجلسة في قاعدة البيانات
    
    تحفظ البيانات عند كل تحديث وليس فقط عند الاكتمال
    """
    
    @staticmethod
    def get_or_create_db_session(
        session_id: str,
        user_identifier: str,
        channel: str = 'whatsapp'
    ) -> 'ConversationSession':
        """
        جلب أو إنشاء جلسة في قاعدة البيانات
        """
        from .models import ConversationSession, ConversationStatus, ChannelType
        
        # تحويل channel للقيمة الصحيحة
        channel_map = {
            'whatsapp': ChannelType.WHATSAPP,
            'web_chat': ChannelType.WEB_CHAT,
            'api': ChannelType.API,
            'mobile_app': ChannelType.MOBILE_APP,
        }
        channel_value = channel_map.get(channel, ChannelType.WHATSAPP)
        
        session, created = ConversationSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user_identifier': user_identifier,
                'channel': channel_value,
                'status': ConversationStatus.ACTIVE,
                'expires_at': timezone.now() + timedelta(hours=24),
            }
        )
        
        if created:
            logger.info(f"💾 Created DB session: {session_id[:8]}...")
        
        return session
    
    @staticmethod
    def update_session_stage(
        session_id: str,
        new_stage: str,
        trigger_type: str = 'ai_decision',
        trigger_message_id: str = None,
        data_snapshot: Dict = None
    ) -> bool:
        """
        تحديث مرحلة الجلسة وتسجيل الانتقال
        """
        from .models import (
            ConversationSession, StageTransition, 
            ConversationMessage, ConversationStage
        )
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            old_stage = session.current_stage
            
            # لا تسجل إذا لم تتغير المرحلة
            if old_stage == new_stage:
                return True
            
            with transaction.atomic():
                # تحديث الجلسة
                session.previous_stage = old_stage
                session.current_stage = new_stage
                session.stage_transitions_count += 1
                session.last_activity_at = timezone.now()
                session.save()
                
                # جلب الرسالة المحفزة إن وجدت
                trigger_msg = None
                if trigger_message_id:
                    try:
                        trigger_msg = ConversationMessage.objects.get(
                            message_id=trigger_message_id
                        )
                    except ConversationMessage.DoesNotExist:
                        pass
                
                # تسجيل الانتقال
                StageTransition.objects.create(
                    session=session,
                    from_stage=old_stage,
                    to_stage=new_stage,
                    trigger_type=trigger_type,
                    trigger_message=trigger_msg,
                    is_successful=True,
                    data_snapshot=data_snapshot or {}
                )
            
            logger.info(f"📍 DB Stage: {old_stage} → {new_stage}")
            return True
            
        except ConversationSession.DoesNotExist:
            logger.warning(f"⚠️ Session not found in DB: {session_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating stage: {e}")
            return False
    
    @staticmethod
    def save_message(
        session_id: str,
        role: str,
        content: str,
        message_type: str = 'text',
        extracted_data: Dict = None,
        ai_analysis: Dict = None,
        metadata: Dict = None
    ) -> Optional[str]:
        """
        حفظ رسالة في قاعدة البيانات
        
        Returns:
            message_id أو None
        """
        from .models import (
            ConversationSession, ConversationMessage,
            MessageRole, MessageType
        )
        import uuid
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            # تحويل role
            role_map = {
                'user': MessageRole.USER,
                'assistant': MessageRole.ASSISTANT,
                'system': MessageRole.SYSTEM,
            }
            role_value = role_map.get(role, MessageRole.USER)
            
            # تحويل message_type
            type_map = {
                'text': MessageType.TEXT,
                'image': MessageType.IMAGE,
                'document': MessageType.DOCUMENT,
                'location': MessageType.LOCATION,
                'button_response': MessageType.BUTTON_RESPONSE,
                'list_response': MessageType.LIST_RESPONSE,
            }
            type_value = type_map.get(message_type, MessageType.TEXT)
            
            message_id = str(uuid.uuid4())
            
            with transaction.atomic():
                ConversationMessage.objects.create(
                    session=session,
                    message_id=message_id,
                    role=role_value,
                    message_type=type_value,
                    content=content,
                    stage_at_message=session.current_stage,
                    extracted_data=extracted_data,
                    ai_analysis=ai_analysis,
                    metadata=metadata or {}
                )
                
                # تحديث عداد الرسائل
                session.message_count += 1
                session.last_activity_at = timezone.now()
                session.save(update_fields=['message_count', 'last_activity_at', 'updated_at'])
            
            logger.debug(f"💬 Saved message: {role} - {content[:50]}...")
            return message_id
            
        except ConversationSession.DoesNotExist:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Error saving message: {e}")
            return None
    
    @staticmethod
    def update_vehicle_data(
        session_id: str,
        brand: str = None,
        model: str = None,
        year: int = None,
        value: float = None,
        plate_no: str = None,
        service_type: str = None,
        is_confirmed: bool = None
    ) -> bool:
        """
        تحديث بيانات السيارة في قاعدة البيانات
        """
        from .models import ConversationSession, SessionVehicleData
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            # جلب أو إنشاء بيانات السيارة
            vehicle_data, created = SessionVehicleData.objects.get_or_create(
                session=session
            )
            
            # تحديث الحقول غير الفارغة
            if brand is not None:
                vehicle_data.brand = brand
            if model is not None:
                vehicle_data.model = model
            if year is not None:
                vehicle_data.year = year
            if value is not None:
                vehicle_data.value = Decimal(str(value))
            if plate_no is not None:
                vehicle_data.plate_no = plate_no
            if service_type is not None:
                vehicle_data.service_type = service_type
            if is_confirmed is not None:
                vehicle_data.is_confirmed = is_confirmed
                if is_confirmed:
                    vehicle_data.confirmed_at = timezone.now()
            
            vehicle_data.save()
            
            # تحديث وقت النشاط
            session.last_activity_at = timezone.now()
            session.save(update_fields=['last_activity_at', 'updated_at'])
            
            logger.debug(f"🚗 Updated vehicle data for session {session_id[:8]}...")
            return True
            
        except ConversationSession.DoesNotExist:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating vehicle data: {e}")
            return False
    
    @staticmethod
    def update_profile_data(
        session_id: str,
        national_id: str = None,
        birth_date: str = None,
        full_name: str = None,
        phone: str = None,
        email: str = None,
        city: str = None,
        is_confirmed: bool = None
    ) -> bool:
        """
        تحديث بيانات العميل في قاعدة البيانات
        """
        from .models import ConversationSession, SessionProfileData
        from datetime import datetime as dt
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            # جلب أو إنشاء بيانات العميل
            profile_data, created = SessionProfileData.objects.get_or_create(
                session=session
            )
            
            # تحديث الحقول غير الفارغة
            if national_id is not None:
                profile_data.national_id = national_id
            if birth_date is not None:
                # تحويل التاريخ إذا كان string
                if isinstance(birth_date, str):
                    try:
                        profile_data.birth_date = dt.strptime(birth_date, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                else:
                    profile_data.birth_date = birth_date
            if full_name is not None:
                profile_data.full_name = full_name
            if phone is not None:
                profile_data.phone = phone
            if email is not None:
                profile_data.email = email
            if city is not None:
                profile_data.city = city
            if is_confirmed is not None:
                profile_data.is_confirmed = is_confirmed
                if is_confirmed:
                    profile_data.confirmed_at = timezone.now()
            
            profile_data.save()
            
            # تحديث وقت النشاط
            session.last_activity_at = timezone.now()
            session.save(update_fields=['last_activity_at', 'updated_at'])
            
            logger.debug(f"👤 Updated profile data for session {session_id[:8]}...")
            return True
            
        except ConversationSession.DoesNotExist:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error updating profile data: {e}")
            return False
    
    @staticmethod
    def save_offers_data(
        session_id: str,
        shown_offers: List[Dict] = None,
        selected_offer_id: int = None,
        selected_offer_data: Dict = None,
        is_confirmed: bool = None
    ) -> bool:
        """
        حفظ بيانات العروض في قاعدة البيانات
        """
        from .models import ConversationSession, SessionOffersData
        from insurance_core.models import InsuranceOffer
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            # جلب أو إنشاء بيانات العروض
            offers_data, created = SessionOffersData.objects.get_or_create(
                session=session
            )
            
            if shown_offers is not None:
                offers_data.shown_offers = shown_offers
                offers_data.shown_at = timezone.now()
            
            if selected_offer_id is not None:
                try:
                    offer = InsuranceOffer.objects.get(id=selected_offer_id)
                    offers_data.selected_offer = offer
                except InsuranceOffer.DoesNotExist:
                    pass
                offers_data.selected_at = timezone.now()
            
            if selected_offer_data is not None:
                offers_data.selected_offer_data = selected_offer_data
            
            if is_confirmed is not None:
                offers_data.is_confirmed = is_confirmed
                if is_confirmed:
                    offers_data.confirmed_at = timezone.now()
            
            offers_data.save()
            
            # تحديث وقت النشاط
            session.last_activity_at = timezone.now()
            session.save(update_fields=['last_activity_at', 'updated_at'])
            
            logger.debug(f"📋 Updated offers data for session {session_id[:8]}...")
            return True
            
        except ConversationSession.DoesNotExist:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error saving offers data: {e}")
            return False

    @staticmethod
    def complete_session(
        session_id: str,
        order_id: int = None,
        invoice_id: int = None,
        policy_id: int = None,
        total_amount: float = None
    ) -> bool:
        """
        إكمال الجلسة وربطها بالنتائج
        """
        from .models import (
            ConversationSession, SessionResult, 
            ConversationStatus, SessionAnalytics
        )
        from insurance_core.models import InsuranceOrder, Invoice, Policy
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            with transaction.atomic():
                # تحديث حالة الجلسة
                session.status = ConversationStatus.COMPLETED
                session.completed_at = timezone.now()
                
                # ربط الطلب
                if order_id:
                    try:
                        order = InsuranceOrder.objects.get(id=order_id)
                        session.order = order
                    except InsuranceOrder.DoesNotExist:
                        pass
                
                session.save()
                
                # إنشاء أو تحديث نتائج الجلسة
                result, created = SessionResult.objects.get_or_create(
                    session=session
                )
                
                if order_id:
                    try:
                        result.order = InsuranceOrder.objects.get(id=order_id)
                        result.is_order_created = True
                        result.order_created_at = timezone.now()
                    except InsuranceOrder.DoesNotExist:
                        pass
                
                if invoice_id:
                    try:
                        result.invoice = Invoice.objects.get(id=invoice_id)
                        result.is_invoice_created = True
                        result.invoice_created_at = timezone.now()
                    except Invoice.DoesNotExist:
                        pass
                
                if policy_id:
                    try:
                        result.policy = Policy.objects.get(id=policy_id)
                        result.is_policy_issued = True
                        result.policy_issued_at = timezone.now()
                    except Policy.DoesNotExist:
                        pass
                
                if total_amount:
                    result.total_amount = Decimal(str(total_amount))
                
                result.save()
                
                # إنشاء أو تحديث التحليلات
                analytics, _ = SessionAnalytics.objects.get_or_create(
                    session=session
                )
                analytics.calculate_duration()
                
                # حساب إحصائيات الرسائل
                from .models import ConversationMessage, MessageRole
                user_msgs = session.messages.filter(role=MessageRole.USER).count()
                assistant_msgs = session.messages.filter(role=MessageRole.ASSISTANT).count()
                analytics.user_messages_count = user_msgs
                analytics.assistant_messages_count = assistant_msgs
                
                # المراحل المزارة
                stages = list(session.stage_transitions.values_list('to_stage', flat=True))
                analytics.stages_visited = list(set(stages))
                
                analytics.save()
            
            logger.info(f"✅ Session {session_id[:8]}... completed in DB")
            return True
            
        except ConversationSession.DoesNotExist:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error completing session: {e}")
            return False
    
    @staticmethod
    def mark_session_abandoned(session_id: str, drop_off_stage: str = None) -> bool:
        """
        تحديد الجلسة كمتروكة
        """
        from .models import ConversationSession, ConversationStatus, SessionAnalytics
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            with transaction.atomic():
                session.status = ConversationStatus.ABANDONED
                session.save()
                
                # تحديث التحليلات
                analytics, _ = SessionAnalytics.objects.get_or_create(
                    session=session
                )
                if drop_off_stage:
                    analytics.drop_off_stage = drop_off_stage
                analytics.calculate_duration()
                analytics.save()
            
            logger.info(f"🚫 Session {session_id[:8]}... marked as abandoned")
            return True
            
        except ConversationSession.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"❌ Error marking abandoned: {e}")
            return False
    
    @staticmethod
    def mark_session_expired(session_id: str) -> bool:
        """
        تحديد الجلسة كمنتهية
        """
        from .models import ConversationSession, ConversationStatus
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            session.status = ConversationStatus.EXPIRED
            session.save()
            
            logger.info(f"⏰ Session {session_id[:8]}... marked as expired")
            return True
            
        except ConversationSession.DoesNotExist:
            return False
    
    @staticmethod
    def save_modification_event(
        session_id: str,
        event_type: str,
        stage_at_event: str,
        target_stage: str,
        data_before: Dict = None,
        data_after: Dict = None,
        reason: str = None,
        trigger_message: str = None,
        system_response: str = None,
        is_successful: bool = True,
        metadata: Dict = None
    ) -> bool:
        """
        حفظ حدث تعديل/رجوع/إلغاء في قاعدة البيانات
        
        Args:
            session_id: معرف الجلسة
            event_type: نوع الحدث (cancel, edit_vehicle, edit_profile, change_offer, go_back, restart)
            stage_at_event: المرحلة عند الحدث
            target_stage: المرحلة المستهدفة
            data_before: البيانات قبل التعديل
            data_after: البيانات بعد التعديل
            reason: سبب التعديل
            trigger_message: رسالة المستخدم
            system_response: رد النظام
            is_successful: هل نجح التعديل
            metadata: بيانات إضافية
        
        Returns:
            bool: نجاح العملية
        """
        from .models import (
            ConversationSession, SessionModificationEvent,
            ModificationEventType, SessionAnalytics
        )
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            # تحويل event_type للقيمة الصحيحة
            event_type_map = {
                'cancel': ModificationEventType.CANCEL,
                'edit_vehicle': ModificationEventType.EDIT_VEHICLE,
                'edit_profile': ModificationEventType.EDIT_PROFILE,
                'change_offer': ModificationEventType.CHANGE_OFFER,
                'go_back': ModificationEventType.GO_BACK,
                'restart': ModificationEventType.RESTART,
            }
            event_type_value = event_type_map.get(event_type, ModificationEventType.GO_BACK)
            
            with transaction.atomic():
                # إنشاء حدث التعديل
                SessionModificationEvent.objects.create(
                    session=session,
                    event_type=event_type_value,
                    stage_at_event=stage_at_event,
                    target_stage=target_stage,
                    data_before=data_before or {},
                    data_after=data_after or {},
                    reason=reason,
                    trigger_message=trigger_message,
                    system_response=system_response,
                    is_successful=is_successful,
                    metadata=metadata or {}
                )
                
                # تحديث إحصائيات التعديلات
                analytics, _ = SessionAnalytics.objects.get_or_create(session=session)
                analytics.total_modifications += 1
                
                # تحديث العداد المناسب
                if event_type == 'cancel':
                    analytics.cancel_count += 1
                elif event_type == 'edit_vehicle':
                    analytics.edit_vehicle_count += 1
                elif event_type == 'edit_profile':
                    analytics.edit_profile_count += 1
                elif event_type == 'change_offer':
                    analytics.change_offer_count += 1
                elif event_type == 'go_back':
                    analytics.go_back_count += 1
                elif event_type == 'restart':
                    analytics.cancel_count += 1  # restart يعتبر إلغاء
                
                analytics.save()
                
                # تحديث وقت النشاط
                session.last_activity_at = timezone.now()
                session.save(update_fields=['last_activity_at', 'updated_at'])
            
            logger.info(f"📝 Saved modification event: {event_type} at {stage_at_event} → {target_stage}")
            return True
            
        except ConversationSession.DoesNotExist:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error saving modification event: {e}")
            return False
    
    @staticmethod
    def mark_session_cancelled(session_id: str, reason: str = None) -> bool:
        """
        تحديد الجلسة كملغاة
        """
        from .models import ConversationSession, ConversationStatus, SessionAnalytics
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            with transaction.atomic():
                session.status = ConversationStatus.CANCELLED
                session.save()
                
                # تحديث التحليلات
                analytics, _ = SessionAnalytics.objects.get_or_create(session=session)
                analytics.drop_off_stage = session.current_stage
                analytics.calculate_duration()
                analytics.save()
            
            logger.info(f"🚫 Session {session_id[:8]}... marked as cancelled")
            return True
            
        except ConversationSession.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"❌ Error marking cancelled: {e}")
            return False
    
    @staticmethod
    def get_modification_history(session_id: str) -> List[Dict]:
        """
        الحصول على سجل التعديلات للجلسة
        """
        from .models import ConversationSession, SessionModificationEvent
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            events = session.modification_events.all().order_by('-created_at')
            
            return [
                {
                    'event_type': event.event_type,
                    'event_type_display': event.get_event_type_display(),
                    'stage_at_event': event.stage_at_event,
                    'target_stage': event.target_stage,
                    'data_before': event.data_before,
                    'data_after': event.data_after,
                    'reason': event.reason,
                    'trigger_message': event.trigger_message,
                    'is_successful': event.is_successful,
                    'created_at': event.created_at.isoformat(),
                }
                for event in events
            ]
            
        except ConversationSession.DoesNotExist:
            return []
        except Exception as e:
            logger.error(f"❌ Error getting modification history: {e}")
            return []
    
    @staticmethod
    def get_session_summary(session_id: str) -> Optional[Dict]:
        """
        الحصول على ملخص الجلسة من قاعدة البيانات
        """
        from .models import ConversationSession
        
        try:
            session = ConversationSession.objects.select_related(
                'vehicle_data', 'profile_data', 'offers_data', 'result', 'analytics'
            ).get(session_id=session_id)
            
            summary = {
                'session_id': str(session.session_id),
                'user_identifier': session.user_identifier,
                'channel': session.channel,
                'status': session.status,
                'current_stage': session.current_stage,
                'message_count': session.message_count,
                'stage_transitions_count': session.stage_transitions_count,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
            }
            
            # بيانات السيارة
            if hasattr(session, 'vehicle_data'):
                vd = session.vehicle_data
                summary['vehicle'] = {
                    'brand': vd.brand,
                    'model': vd.model,
                    'year': vd.year,
                    'value': float(vd.value) if vd.value else None,
                    'plate_no': vd.plate_no,
                    'is_complete': vd.is_complete,
                    'is_confirmed': vd.is_confirmed,
                }
            
            # بيانات العميل
            if hasattr(session, 'profile_data'):
                pd = session.profile_data
                summary['profile'] = {
                    'national_id': pd.national_id,
                    'birth_date': pd.birth_date.isoformat() if pd.birth_date else None,
                    'full_name': pd.full_name,
                    'phone': pd.phone,
                    'is_complete': pd.is_complete,
                    'is_confirmed': pd.is_confirmed,
                }
            
            # بيانات العروض
            if hasattr(session, 'offers_data'):
                od = session.offers_data
                summary['offers'] = {
                    'shown_count': len(od.shown_offers) if od.shown_offers else 0,
                    'selected_offer_id': od.selected_offer_id,
                    'is_confirmed': od.is_confirmed,
                }
            
            # النتائج
            if hasattr(session, 'result'):
                r = session.result
                summary['result'] = {
                    'order_id': r.order_id,
                    'invoice_id': r.invoice_id,
                    'policy_id': r.policy_id,
                    'is_order_created': r.is_order_created,
                    'is_invoice_created': r.is_invoice_created,
                    'is_payment_completed': r.is_payment_completed,
                    'is_policy_issued': r.is_policy_issued,
                    'total_amount': float(r.total_amount) if r.total_amount else None,
                }
            
            return summary
            
        except ConversationSession.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"❌ Error getting summary: {e}")
            return None


# ═══════════════════════════════════════════════════════════════
# Async Wrappers
# ═══════════════════════════════════════════════════════════════

class AsyncSessionPersistenceService:
    """
    نسخة async من خدمة الحفظ
    """
    
    @staticmethod
    async def get_or_create_db_session(
        session_id: str,
        user_identifier: str,
        channel: str = 'whatsapp'
    ):
        return await sync_to_async(
            SessionPersistenceService.get_or_create_db_session
        )(session_id, user_identifier, channel)
    
    @staticmethod
    async def update_session_stage(
        session_id: str,
        new_stage: str,
        trigger_type: str = 'ai_decision',
        trigger_message_id: str = None,
        data_snapshot: Dict = None
    ) -> bool:
        return await sync_to_async(
            SessionPersistenceService.update_session_stage
        )(session_id, new_stage, trigger_type, trigger_message_id, data_snapshot)
    
    @staticmethod
    async def save_message(
        session_id: str,
        role: str,
        content: str,
        message_type: str = 'text',
        extracted_data: Dict = None,
        ai_analysis: Dict = None,
        metadata: Dict = None
    ) -> Optional[str]:
        return await sync_to_async(
            SessionPersistenceService.save_message
        )(session_id, role, content, message_type, extracted_data, ai_analysis, metadata)
    
    @staticmethod
    async def update_vehicle_data(session_id: str, **kwargs) -> bool:
        return await sync_to_async(
            SessionPersistenceService.update_vehicle_data
        )(session_id, **kwargs)
    
    @staticmethod
    async def update_profile_data(session_id: str, **kwargs) -> bool:
        return await sync_to_async(
            SessionPersistenceService.update_profile_data
        )(session_id, **kwargs)
    
    @staticmethod
    async def save_offers_data(
        session_id: str,
        shown_offers: List[Dict] = None,
        selected_offer_id: int = None,
        selected_offer_data: Dict = None,
        is_confirmed: bool = None
    ) -> bool:
        return await sync_to_async(
            SessionPersistenceService.save_offers_data
        )(session_id, shown_offers, selected_offer_id, selected_offer_data, is_confirmed)
    
    @staticmethod
    async def complete_session(
        session_id: str,
        order_id: int = None,
        invoice_id: int = None,
        policy_id: int = None,
        total_amount: float = None
    ) -> bool:
        return await sync_to_async(
            SessionPersistenceService.complete_session
        )(session_id, order_id, invoice_id, policy_id, total_amount)
    
    @staticmethod
    async def mark_session_abandoned(session_id: str, drop_off_stage: str = None) -> bool:
        return await sync_to_async(
            SessionPersistenceService.mark_session_abandoned
        )(session_id, drop_off_stage)
    
    @staticmethod
    async def save_modification_event(
        session_id: str,
        event_type: str,
        stage_at_event: str,
        target_stage: str,
        data_before: Dict = None,
        data_after: Dict = None,
        reason: str = None,
        trigger_message: str = None,
        system_response: str = None,
        is_successful: bool = True,
        metadata: Dict = None
    ) -> bool:
        return await sync_to_async(
            SessionPersistenceService.save_modification_event
        )(
            session_id, event_type, stage_at_event, target_stage,
            data_before, data_after, reason, trigger_message,
            system_response, is_successful, metadata
        )
    
    @staticmethod
    async def mark_session_cancelled(session_id: str, reason: str = None) -> bool:
        return await sync_to_async(
            SessionPersistenceService.mark_session_cancelled
        )(session_id, reason)
    
    @staticmethod
    async def get_modification_history(session_id: str) -> List[Dict]:
        return await sync_to_async(
            SessionPersistenceService.get_modification_history
        )(session_id)
    
    @staticmethod
    async def get_session_summary(session_id: str) -> Optional[Dict]:
        return await sync_to_async(
            SessionPersistenceService.get_session_summary
        )(session_id)


# ═══════════════════════════════════════════════════════════════
# Singleton Access
# ═══════════════════════════════════════════════════════════════

_persistence_service: Optional[SessionPersistenceService] = None
_async_persistence_service: Optional[AsyncSessionPersistenceService] = None


def get_persistence_service() -> SessionPersistenceService:
    """الحصول على خدمة الحفظ"""
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = SessionPersistenceService()
    return _persistence_service


def get_async_persistence_service() -> AsyncSessionPersistenceService:
    """الحصول على خدمة الحفظ async"""
    global _async_persistence_service
    if _async_persistence_service is None:
        _async_persistence_service = AsyncSessionPersistenceService()
    return _async_persistence_service
