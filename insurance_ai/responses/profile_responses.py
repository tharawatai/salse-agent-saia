"""
ProfileResponses - ردود البيانات الشخصية
"""
from typing import Dict, Any

from ..context_models import ConversationContext
from .message_formatter import MessageFormatter


class ProfileResponses:
    """مولد ردود البيانات الشخصية"""
    
    @staticmethod
    async def generate_vehicle_data_status(context: ConversationContext) -> str:
        """
        توليد حالة بيانات السيارة المطلوبة مع علامات ✅ و ❌ - متوافق مع واتساب
        
        Args:
            context: سياق المحادثة
        
        Returns:
            str: الرد مع حالة كل حقل
        """
        return MessageFormatter.format_vehicle_status(context.vehicle_data)
    
    @staticmethod
    async def generate_profile_data_status(context: ConversationContext) -> str:
        """
        توليد حالة البيانات الشخصية المطلوبة مع علامات ✅ و ❌ - متوافق مع واتساب
        
        Args:
            context: سياق المحادثة
        
        Returns:
            str: الرد مع حالة كل حقل
        """
        return MessageFormatter.format_profile_status(context.profile_data)
    
    @staticmethod
    async def generate_profile_request() -> str:
        """
        توليد رد طلب بيانات العميل
        
        Returns:
            str: الرد
        """
        return """📝 لإتمام طلبك، أحتاج منك:
• رقم الهوية الوطنية (10 أرقام)
• تاريخ الميلاد (مثل: 1990-01-15)

يمكنك إرسالها في رسالة واحدة."""
    
    @staticmethod
    async def generate_profile_confirmation(context: ConversationContext) -> str:
        """
        توليد رد تأكيد البيانات الشخصية - متوافق مع واتساب
        
        Args:
            context: سياق المحادثة
        
        Returns:
            str: الرد
        """
        return MessageFormatter.format_profile_confirmation(
            context.profile_data, 
            context.phone
        )
    
    @staticmethod
    async def generate_vehicle_confirmation(context: ConversationContext) -> str:
        """
        توليد رد تأكيد بيانات السيارة - متوافق مع واتساب
        
        Args:
            context: سياق المحادثة
        
        Returns:
            str: الرد
        """
        return MessageFormatter.format_vehicle_confirmation(context.vehicle_data)
    
    @staticmethod
    async def generate_order_summary(context: ConversationContext) -> str:
        """
        توليد ملخص الطلب الكامل - متوافق مع واتساب
        
        Args:
            context: سياق المحادثة
        
        Returns:
            str: الرد
        """
        return MessageFormatter.format_order_summary(
            context.vehicle_data,
            context.profile_data,
            context.selected_offer or {}
        )
