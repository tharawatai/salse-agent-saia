"""
OffersResponses - ردود العروض
"""
import logging
from typing import List, Dict, Any

from asgiref.sync import sync_to_async

from ..cache_manager import get_insurance_cache
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class OffersResponses:
    """مولد ردود العروض"""
    
    @staticmethod
    async def generate_offers_list(offers: List[Dict]) -> str:
        """
        توليد قائمة العروض - متوافق مع واتساب
        
        Args:
            offers: قائمة العروض
        
        Returns:
            str: الرد المنسق
        """
        return MessageFormatter.format_offers_list(offers)
    
    @staticmethod
    async def generate_offer_details(offer: Dict, num: int) -> str:
        """
        توليد تفاصيل العرض الكاملة - متوافق مع واتساب
        
        Args:
            offer: بيانات العرض
            num: رقم العرض
        
        Returns:
            str: الرد المنسق
        """
        # جلب تفاصيل العرض الكاملة من الكاش/DB
        insurance_cache = get_insurance_cache()
        offer_id = offer.get('id')
        
        if offer_id:
            full_offer = await sync_to_async(insurance_cache.get_offer_details)(offer_id)
            if full_offer:
                offer = full_offer
                logger.info(f"📦 Loaded full offer details from DB: {offer_id}")
        
        return MessageFormatter.format_offer_details(offer, num)
    
    @staticmethod
    async def generate_offer_confirmation(offer: Dict, num: int) -> str:
        """
        توليد رد تأكيد اختيار العرض
        
        Args:
            offer: بيانات العرض
            num: رقم العرض
        
        Returns:
            str: الرد
        """
        return f"""✅ ممتاز! اخترت العرض رقم {num} من {offer.get('company', '')} بسعر {offer.get('final_price', 0):.0f} ريال.

📝 لإتمام الطلب، أحتاج منك:
• رقم الهوية الوطنية (10 أرقام)
• تاريخ الميلاد"""
