"""
Insurance Tools
أدوات مستقلة يمكن استخدامها مع أي مساعد
"""
import logging
from typing import Dict, Optional
from decimal import Decimal
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


async def get_services_tool() -> Dict:
    """
    جلب الخدمات المتاحة من قاعدة البيانات
    
    Returns:
        Dict مع قائمة الخدمات
    """
    from insurance_core.models import InsuranceService
    
    @sync_to_async
    def fetch():
        services = InsuranceService.objects.filter(is_active=True)
        return {
            'success': True,
            'count': services.count(),
            'services': [
                {
                    'id': s.id,
                    'name_ar': s.name_ar,
                    'name_en': s.name_en,
                    'type': s.service_type,
                    'description': s.description_ar,
                    'base_price': float(s.base_price) if s.base_price else 0,
                }
                for s in services
            ]
        }
    
    try:
        return await fetch()
    except Exception as e:
        logger.exception(f"Error fetching services: {e}")
        return {'success': False, 'error': str(e)}


async def get_offers_tool(
    service_type: str = 'comprehensive',
    vehicle_year: Optional[int] = None,
    vehicle_value: Optional[float] = None
) -> Dict:
    """
    جلب عروض التأمين المتاحة
    
    Args:
        service_type: نوع التأمين (comprehensive/third_party)
        vehicle_year: سنة الصنع
        vehicle_value: قيمة السيارة
        
    Returns:
        Dict مع قائمة العروض
    """
    from ...database import OffersRepository
    
    try:
        offers = await OffersRepository.fetch_offers(
            service_type=service_type,
            vehicle_year=vehicle_year,
            vehicle_value=Decimal(str(vehicle_value)) if vehicle_value else None
        )
        
        return {
            'success': True,
            'count': len(offers),
            'offers': offers
        }
    except Exception as e:
        logger.exception(f"Error fetching offers: {e}")
        return {'success': False, 'error': str(e)}


async def create_order_tool(
    offer_id: int,
    vehicle_data: Dict,
    profile_data: Dict,
    phone: str = None
) -> Dict:
    """
    إنشاء طلب تأمين جديد
    
    Args:
        offer_id: معرف العرض المختار
        vehicle_data: بيانات السيارة
        profile_data: بيانات العميل
        phone: رقم الهاتف
        
    Returns:
        Dict مع تفاصيل الطلب
    """
    from ...database import OrdersRepository
    from ...context_models import ConversationContext
    from ...ai_intent_analyzer import ConversationStage
    
    try:
        # بناء context
        context = ConversationContext(
            conversation_id="api_call",
            current_stage=ConversationStage.ORDER_SUMMARY
        )
        context.vehicle_data = vehicle_data
        context.profile_data = profile_data
        context.selected_offer_id = offer_id
        context.phone = phone or profile_data.get('phone')
        
        result = await OrdersRepository.create_order_and_invoice(context)
        return result
        
    except Exception as e:
        logger.exception(f"Error creating order: {e}")
        return {'success': False, 'error': str(e)}


async def get_order_status_tool(order_id: int) -> Dict:
    """
    جلب حالة طلب
    
    Args:
        order_id: معرف الطلب
        
    Returns:
        Dict مع حالة الطلب
    """
    from insurance_core.models import InsuranceOrder
    
    @sync_to_async
    def fetch():
        try:
            order = InsuranceOrder.objects.select_related(
                'user', 'vehicle', 'offer', 'offer__company'
            ).get(id=order_id)
            
            return {
                'success': True,
                'order': {
                    'id': order.id,
                    'code': order.order_code,
                    'status': order.status,
                    'status_display': order.get_status_display(),
                    'total_price': float(order.total_price) if order.total_price else 0,
                    'company': order.offer.company.name_ar if order.offer and order.offer.company else None,
                    'coverage_type': order.offer.get_coverage_type_display() if order.offer else None,
                    'created_at': order.created_at.isoformat(),
                    'vehicle': {
                        'brand': order.vehicle.brand if order.vehicle else None,
                        'model': order.vehicle.model if order.vehicle else None,
                        'year': order.vehicle.model_year if order.vehicle else None,
                    } if order.vehicle else None,
                }
            }
        except InsuranceOrder.DoesNotExist:
            return {'success': False, 'error': 'الطلب غير موجود'}
    
    try:
        return await fetch()
    except Exception as e:
        logger.exception(f"Error fetching order: {e}")
        return {'success': False, 'error': str(e)}
