"""
OrdersRepository - إنشاء الطلبات والفواتير
مع retry logic لحل مشكلة database is locked في SQLite
"""
import logging
import time
from typing import Dict, Any
from decimal import Decimal
from functools import wraps

from asgiref.sync import sync_to_async
from django.db import OperationalError, close_old_connections

from insurance_core.models import InsuranceOffer
from ..database_manager import database_manager
from ..context_models import ConversationContext

logger = logging.getLogger(__name__)


def with_db_retry(max_retries: int = 5, base_delay: float = 0.1):
    """
    Decorator لإعادة المحاولة عند حدوث database is locked
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    close_old_connections()
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e):
                        last_error = e
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"⚠️ Database locked, retry {attempt + 1}/{max_retries} after {delay:.2f}s")
                        time.sleep(delay)
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator


class OrdersRepository:
    """مستودع الطلبات مع retry logic"""
    
    @staticmethod
    @with_db_retry(max_retries=5, base_delay=0.1)
    def _get_or_create_user_sync(national_id, phone, birth_date):
        """إنشاء المستخدم مع retry"""
        return database_manager.get_or_create_user(
            national_id=national_id,
            phone=phone,
            birth_date=birth_date,
        )
    
    @staticmethod
    @with_db_retry(max_retries=5, base_delay=0.1)
    def _get_or_create_vehicle_sync(user, plate_no, brand, model, model_year, vehicle_value):
        """إنشاء السيارة مع retry"""
        return database_manager.get_or_create_vehicle(
            user=user,
            plate_no=plate_no,
            brand=brand,
            model=model,
            model_year=model_year,
            vehicle_value=vehicle_value
        )
    
    @staticmethod
    @with_db_retry(max_retries=3, base_delay=0.05)
    def _get_offer_sync(offer_id):
        """جلب العرض مع retry"""
        return InsuranceOffer.objects.get(id=offer_id)
    
    @staticmethod
    @with_db_retry(max_retries=5, base_delay=0.1)
    def _create_order_sync(user, offer, vehicle, has_njm_discount):
        """إنشاء الطلب مع retry"""
        return database_manager.create_order(
            user=user,
            offer=offer,
            vehicle=vehicle,
            has_njm_discount=has_njm_discount
        )
    
    @staticmethod
    @with_db_retry(max_retries=5, base_delay=0.1)
    def _create_invoice_sync(order):
        """إنشاء الفاتورة مع retry"""
        return database_manager.create_invoice(order)
    
    @staticmethod
    async def create_order_and_invoice(context: ConversationContext) -> Dict[str, Any]:
        """
        إنشاء الطلب والفاتورة
        
        Args:
            context: سياق المحادثة
        
        Returns:
            Dict: نتيجة الإنشاء
        """
        try:
            v = context.vehicle_data
            p = context.profile_data
            
            # إنشاء أو جلب المستخدم مع retry
            user, _ = await sync_to_async(OrdersRepository._get_or_create_user_sync)(
                national_id=p.get('national_id'),
                phone=context.phone or '0500000000',
                birth_date=p.get('birth_date'),
            )
            
            # إنشاء أو جلب السيارة مع retry
            vehicle, _ = await sync_to_async(OrdersRepository._get_or_create_vehicle_sync)(
                user=user,
                plate_no=v.get('plate_no'),
                brand=v.get('brand'),
                model=v.get('model'),
                model_year=v.get('year'),
                vehicle_value=Decimal(str(v.get('value', 0)))
            )
            
            # جلب العرض مع retry
            offer_id = context.selected_offer_id
            offer = await sync_to_async(OrdersRepository._get_offer_sync)(offer_id)
            
            # إنشاء الطلب مع retry
            order = await sync_to_async(OrdersRepository._create_order_sync)(
                user=user,
                offer=offer,
                vehicle=vehicle,
                has_njm_discount=True
            )
            
            # إنشاء الفاتورة مع retry
            invoice = await sync_to_async(OrdersRepository._create_invoice_sync)(order)
            
            logger.info(f"✅ Order: {order.order_code}, Invoice: {invoice.invoice_no}")
            
            return {
                'success': True,
                'order_id': order.id,
                'order_code': order.order_code,
                'invoice_id': invoice.id,
                'invoice_no': invoice.invoice_no,
                'amount': float(invoice.amount)
            }
            
        except OperationalError as e:
            if "database is locked" in str(e):
                logger.error(f"❌ Database locked error persists: {e}")
                return {
                    'success': False, 
                    'error': 'قاعدة البيانات مشغولة، يرجى المحاولة مرة أخرى بعد قليل'
                }
            raise
        except Exception as e:
            logger.error(f"❌ Error creating order: {e}")
            return {'success': False, 'error': str(e)}
