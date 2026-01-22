"""
OffersRepository - جلب العروض من قاعدة البيانات
مع retry logic لحل مشكلة database is locked في SQLite
"""
import logging
import time
from typing import List, Dict, Any, Optional
from decimal import Decimal
from functools import wraps

from asgiref.sync import sync_to_async
from django.db import OperationalError, close_old_connections

from ..database_manager import database_manager

logger = logging.getLogger(__name__)


def with_db_retry(max_retries: int = 3, base_delay: float = 0.05):
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


class OffersRepository:
    """مستودع العروض مع retry logic"""
    
    @staticmethod
    @with_db_retry(max_retries=3, base_delay=0.05)
    def _get_offers_sync(service_type, vehicle_year, vehicle_value, limit):
        """جلب العروض مع retry"""
        return database_manager.get_offers(
            service_type=service_type,
            vehicle_year=vehicle_year,
            vehicle_value=vehicle_value,
            limit=limit
        )
    
    @staticmethod
    @with_db_retry(max_retries=3, base_delay=0.05)
    def _format_offer_sync(offer, has_njm):
        """تنسيق العرض مع retry"""
        return database_manager.format_offer_for_display(offer, has_njm=has_njm)
    
    @staticmethod
    async def fetch_offers(
        service_type: str = 'comprehensive',
        vehicle_year: int = None,
        vehicle_value: Decimal = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        جلب العروض من قاعدة البيانات
        
        Args:
            service_type: نوع التأمين
            vehicle_year: سنة السيارة
            vehicle_value: قيمة السيارة
            limit: الحد الأقصى للعروض
        
        Returns:
            List[Dict]: قائمة العروض
        """
        try:
            # تحويل نوع الخدمة للقيمة الصحيحة في DB
            service_type_mapping = {
                'شامل': 'comprehensive',
                'comprehensive': 'comprehensive',
                'ضد الغير': 'tpl',
                'tpl': 'tpl',
                'third_party': 'tpl',
            }
            service_type = service_type_mapping.get(service_type, 'comprehensive')
            
            logger.info(f"🔍 Fetching offers: service_type={service_type}, year={vehicle_year}, value={vehicle_value}")
            
            offers = await sync_to_async(OffersRepository._get_offers_sync)(
                service_type=service_type,
                vehicle_year=vehicle_year,
                vehicle_value=vehicle_value,
                limit=limit
            )
            
            formatted_offers = []
            for offer in offers:
                formatted = await sync_to_async(OffersRepository._format_offer_sync)(offer, has_njm=True)
                formatted_offers.append(formatted)
            
            logger.info(f"📋 Fetched {len(formatted_offers)} offers")
            return formatted_offers
            
        except OperationalError as e:
            if "database is locked" in str(e):
                logger.error(f"❌ Database locked error: {e}")
                return []
            raise
        except Exception as e:
            logger.error(f"❌ Error fetching offers: {e}")
            return []
    
    @staticmethod
    async def get_offer_by_id(offer_id: int) -> Optional[Dict]:
        """
        جلب عرض بالمعرف
        
        Args:
            offer_id: معرف العرض
        
        Returns:
            Dict أو None
        """
        try:
            from insurance_core.models import InsuranceOffer
            
            @with_db_retry(max_retries=3, base_delay=0.05)
            def get_offer():
                return InsuranceOffer.objects.get(id=offer_id)
            
            offer = await sync_to_async(get_offer)()
            formatted = await sync_to_async(OffersRepository._format_offer_sync)(offer, has_njm=True)
            return formatted
            
        except OperationalError as e:
            if "database is locked" in str(e):
                logger.error(f"❌ Database locked error: {e}")
                return None
            raise
        except Exception as e:
            logger.error(f"❌ Error getting offer {offer_id}: {e}")
            return None
