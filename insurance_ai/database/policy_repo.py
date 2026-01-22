"""
PolicyRepository - إنشاء وثائق التأمين
مع retry logic لحل مشكلة database is locked في SQLite
"""
import logging
import asyncio
import time
from typing import Dict, Any
from functools import wraps

from asgiref.sync import sync_to_async
from django.db import OperationalError, close_old_connections

from insurance_core.models import InsuranceOrder
from ..database_manager import database_manager
from ..context_models import ConversationContext

logger = logging.getLogger(__name__)


def with_db_retry(max_retries: int = 5, base_delay: float = 0.1):
    """
    Decorator لإعادة المحاولة عند حدوث database is locked
    يستخدم exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    # إغلاق الاتصالات القديمة قبل المحاولة
                    close_old_connections()
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e):
                        last_error = e
                        delay = base_delay * (2 ** attempt)  # exponential backoff
                        logger.warning(f"⚠️ Database locked, retry {attempt + 1}/{max_retries} after {delay:.2f}s")
                        time.sleep(delay)
                    else:
                        raise
            # إذا فشلت كل المحاولات
            logger.error(f"❌ Database still locked after {max_retries} retries")
            raise last_error
        return wrapper
    return decorator


class PolicyRepository:
    """مستودع الوثائق مع retry logic"""
    
    @staticmethod
    @with_db_retry(max_retries=5, base_delay=0.1)
    def _process_payment_sync(invoice):
        """معالجة الدفع مع retry"""
        return database_manager.process_payment(invoice)
    
    @staticmethod
    @with_db_retry(max_retries=5, base_delay=0.1)
    def _issue_policy_sync(order):
        """إصدار الوثيقة مع retry"""
        return database_manager.issue_policy(order)
    
    @staticmethod
    @with_db_retry(max_retries=3, base_delay=0.05)
    def _get_order_sync(order_id):
        """جلب الطلب مع retry"""
        return InsuranceOrder.objects.select_related('invoice').get(id=order_id)
    
    @staticmethod
    async def create_policy(context: ConversationContext) -> Dict[str, Any]:
        """
        إنشاء وثيقة التأمين
        
        Args:
            context: سياق المحادثة
        
        Returns:
            Dict: نتيجة الإنشاء
        """
        try:
            order_id = context.order_id
            
            # جلب الطلب مع retry
            order = await sync_to_async(PolicyRepository._get_order_sync)(order_id)
            
            # جلب الفاتورة
            invoice = await sync_to_async(lambda: order.invoice)()
            
            # معالجة الدفع مع retry
            await sync_to_async(PolicyRepository._process_payment_sync)(invoice)
            
            # إعادة جلب الطلب بعد الدفع (للتأكد من التحديث)
            order = await sync_to_async(PolicyRepository._get_order_sync)(order_id)
            
            # إصدار الوثيقة مع retry
            policy = await sync_to_async(PolicyRepository._issue_policy_sync)(order)
            
            logger.info(f"✅ Policy issued: {policy.policy_no}")
            
            return {
                'success': True,
                'policy_id': policy.id,
                'policy_no': policy.policy_no,
                'start_date': policy.start_date.isoformat(),
                'end_date': policy.end_date.isoformat(),
                'pdf_url': policy.pdf_url
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
            logger.error(f"❌ Error creating policy: {e}")
            return {'success': False, 'error': str(e)}
