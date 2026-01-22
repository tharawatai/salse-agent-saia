"""
ServicesResponses - ردود الخدمات
"""
import logging
from typing import List, Dict

from asgiref.sync import sync_to_async

from ..database_manager import database_manager
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class ServicesResponses:
    """مولد ردود الخدمات"""
    
    @staticmethod
    async def generate_services_list() -> str:
        """
        توليد قائمة الخدمات من قاعدة البيانات - متوافق مع واتساب
        
        Returns:
            str: الرد المنسق
        """
        try:
            services = await sync_to_async(database_manager.get_insurance_services)()
            
            if not services:
                return """🚗 *خدمات SAIA للتأمين:*

• تأمين شامل - تغطية كاملة للسيارة
• تأمين ضد الغير - تغطية الطرف الثالث

💬 ما نوع التأمين الذي تبحث عنه؟"""
            
            return MessageFormatter.format_services_list(services)
            
        except Exception as e:
            logger.error(f"❌ Error generating services: {e}")
            return """🚗 *خدمات SAIA للتأمين:*

• تأمين شامل - تغطية كاملة للسيارة
• تأمين ضد الغير - تغطية الطرف الثالث

💬 ما نوع التأمين الذي تبحث عنه؟"""
    
    @staticmethod
    def is_asking_about_services(message: str, ai_result: Dict) -> bool:
        """
        التحقق مما إذا كان العميل يسأل عن الخدمات
        
        Args:
            message: الرسالة
            ai_result: نتيجة تحليل AI
        
        Returns:
            bool: هل يسأل عن الخدمات
        """
        message_lower = message.lower()
        message_normalized = message.replace('ي', 'ى').replace('ة', 'ه').replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        intent = ai_result.get('user_intent', '').lower()
        
        service_keywords = [
            # عربي
            'خدمات', 'خدماتكم', 'تقدمون', 'توفرون', 'عندكم',
            'ماذا تقدمون', 'ما هي خدماتكم', 'انواع التأمين',
            'أنواع التأمين', 'انواع التامين', 'ايش عندكم',
            'ايش معاكم', 'ايش لديكم', 'شو عندكم', 'وش عندكم',
            'ايش انواع', 'انواع', 'الانواع', 'نوع التأمين',
            'نوع التامين', 'التامين عندكم', 'التأمين عندكم',
            'ايش التامين', 'ايش التأمين', 'شو التامين',
            # إنجليزي
            'services', 'what do you offer', 'types', 'insurance types'
        ]
        
        for keyword in service_keywords:
            if keyword in message_lower or keyword in message or keyword in message_normalized:
                return True
        
        # التحقق من نية AI
        if 'خدم' in intent or 'service' in intent or 'انواع' in intent or 'types' in intent:
            return True
        
        return False
