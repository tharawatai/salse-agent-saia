"""
PolicyResponses - ردود الوثائق والطلبات - متوافق مع واتساب
"""
from typing import Dict, Any


class PolicyResponses:
    """مولد ردود الوثائق والطلبات"""
    
    @staticmethod
    async def generate_order_created(result: Dict) -> str:
        """
        توليد رد إنشاء الطلب - متوافق مع واتساب
        
        Args:
            result: نتيجة إنشاء الطلب
        
        Returns:
            str: الرد
        """
        return f"""✅ *تم إنشاء طلبك بنجاح!*

📋 رقم الطلب: {result.get('order_code', '')}
🧾 رقم الفاتورة: {result.get('invoice_no', '')}
💰 المبلغ المستحق: {result.get('amount', 0):,.0f} ريال

⏰ الفاتورة صالحة لمدة 24 ساعة

هل تريد الدفع الآن؟"""
    
    @staticmethod
    async def generate_policy_issued(result: Dict) -> str:
        """
        توليد رد إصدار الوثيقة - متوافق مع واتساب
        
        Args:
            result: نتيجة إصدار الوثيقة
        
        Returns:
            str: الرد
        """
        return f"""🎉 *مبروك! تم إصدار وثيقة التأمين بنجاح!*

📄 رقم الوثيقة: {result.get('policy_no', '')}
📅 تاريخ البداية: {result.get('start_date', '')}
📅 تاريخ الانتهاء: {result.get('end_date', '')}

✅ يمكنك تحميل الوثيقة من الرابط المرفق.

شكراً لاختيارك SAIA للتأمين! 🚗
هل تحتاج أي مساعدة أخرى؟"""
    
    @staticmethod
    async def generate_payment_pending() -> str:
        """
        توليد رد انتظار الدفع - متوافق مع واتساب
        
        Returns:
            str: الرد
        """
        return """⏳ *في انتظار تأكيد الدفع...*

بمجرد إتمام الدفع، سيتم إصدار وثيقة التأمين فوراً.

هل تريد المتابعة بالدفع؟"""
