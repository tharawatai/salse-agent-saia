"""
InsuranceAssistant - المساعد الرئيسي للتأمين
يستخدم المحرك الحالي (ProfessionalInsuranceEngineV2) داخلياً
"""
import logging
from typing import Any, Dict, Optional
from decimal import Decimal

from .base import AIAssistant, method_tool
from ..engine.sales_agent import ProfessionalInsuranceEngineV2
from ..context import StageResult

logger = logging.getLogger(__name__)


class InsuranceAssistant(AIAssistant):
    """
    مساعد التأمين الذكي
    يوفر واجهة متوافقة مع django_ai_assistant
    ويستخدم المحرك الاحترافي داخلياً
    """
    
    id = "insurance-assistant"
    name = "مساعد التأمين الذكي - SAIA"
    
    instructions = """
    أنت مساعد تأمين ذكي متخصص في:
    - تأمين السيارات (شامل / ضد الغير)
    - جمع بيانات العميل والسيارة
    - عرض العروض المتاحة
    - إتمام عملية الشراء
    
    تحدث بالعربية بأسلوب ودود ومهني.
    """
    
    model = "gemini-2.0-flash"
    temperature = 0.7
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._engine = ProfessionalInsuranceEngineV2()
        logger.info(f"🚀 InsuranceAssistant initialized")
    
    async def run(
        self,
        message: str,
        thread_id: Any = None,
        phone: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        معالجة رسالة العميل
        
        Args:
            message: رسالة العميل
            thread_id: معرف المحادثة (conversation_id)
            phone: رقم الهاتف
            
        Returns:
            Dict مع response و metadata
        """
        conversation_id = str(thread_id) if thread_id else f"conv_{phone or 'anonymous'}"
        
        logger.info(f"📨 InsuranceAssistant.run: '{message[:50]}...' | thread={conversation_id}")
        
        try:
            result: StageResult = await self._engine.process_message(
                conversation_id=conversation_id,
                message=message,
                user=self._user,
                phone=phone
            )
            
            return {
                'success': result.success,
                'output': result.response_message,
                'stage': result.next_stage.value if result.next_stage else None,
                'data': result.data_collected if hasattr(result, 'data_collected') else {},
                'has_invoice': getattr(result, 'has_invoice', False),
                'invoice_url': getattr(result, 'invoice_url', None),
                'has_policy': getattr(result, 'has_policy', False),
                'policy_url': getattr(result, 'policy_url', None),
            }
            
        except Exception as e:
            logger.exception(f"Error in InsuranceAssistant.run: {e}")
            return {
                'success': False,
                'output': 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.',
                'error': str(e)
            }
    
    # ==================== Tools ====================
    
    @method_tool(description="الحصول على قائمة الخدمات المتاحة")
    async def get_available_services(self) -> Dict:
        """جلب الخدمات المتاحة من قاعدة البيانات"""
        from insurance_core.models import InsuranceService
        from asgiref.sync import sync_to_async
        
        @sync_to_async
        def fetch_services():
            services = InsuranceService.objects.filter(is_active=True)
            return [
                {
                    'id': s.id,
                    'name': s.name_ar,
                    'type': s.service_type,
                    'description': s.description_ar,
                }
                for s in services
            ]
        
        return await fetch_services()
    
    @method_tool(description="الحصول على عروض التأمين المتاحة")
    async def get_insurance_offers(
        self,
        service_type: str = 'comprehensive',
        vehicle_year: int = None,
        vehicle_value: float = None
    ) -> Dict:
        """جلب العروض المتاحة"""
        from ..database import OffersRepository
        
        offers = await OffersRepository.fetch_offers(
            service_type=service_type,
            vehicle_year=vehicle_year,
            vehicle_value=Decimal(str(vehicle_value)) if vehicle_value else None
        )
        
        return {
            'count': len(offers),
            'offers': offers
        }
    
    @method_tool(description="إنشاء طلب تأمين جديد")
    async def create_order(
        self,
        offer_id: int,
        vehicle_data: Dict,
        profile_data: Dict
    ) -> Dict:
        """إنشاء طلب جديد"""
        from ..database import OrdersRepository
        from ..context_models import ConversationContext
        from ..ai_intent_analyzer import ConversationStage
        
        # بناء context مؤقت
        context = ConversationContext(
            conversation_id="tool_call",
            current_stage=ConversationStage.ORDER_SUMMARY
        )
        context.vehicle_data = vehicle_data
        context.profile_data = profile_data
        context.selected_offer_id = offer_id
        context.phone = profile_data.get('phone')
        
        result = await OrdersRepository.create_order_and_invoice(context)
        return result
    
    @method_tool(description="الحصول على حالة طلب")
    async def get_order_status(self, order_id: int) -> Dict:
        """جلب حالة الطلب"""
        from insurance_core.models import InsuranceOrder
        from asgiref.sync import sync_to_async
        
        @sync_to_async
        def fetch_order():
            try:
                order = InsuranceOrder.objects.select_related(
                    'user', 'vehicle', 'offer'
                ).get(id=order_id)
                return {
                    'id': order.id,
                    'code': order.order_code,
                    'status': order.status,
                    'total': float(order.total_price) if order.total_price else 0,
                    'created_at': str(order.created_at),
                }
            except InsuranceOrder.DoesNotExist:
                return {'error': 'الطلب غير موجود'}
        
        return await fetch_order()
