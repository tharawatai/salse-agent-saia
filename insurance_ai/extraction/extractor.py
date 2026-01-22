"""
DataExtractor - استخراج البيانات من الرسائل
"""
import re
import logging
from typing import Dict, Any

from ..context_models import ConversationContext
from .regex_patterns import (
    PLATE_PATTERNS, VALUE_PATTERNS, YEAR_PATTERN,
    NATIONAL_ID_PATTERN, DATE_PATTERNS,
    BRAND_MAPPING, MODEL_MAPPING, SERVICE_TYPE_KEYWORDS
)

logger = logging.getLogger(__name__)


class DataExtractor:
    """استخراج البيانات من الرسائل"""
    
    @staticmethod
    def _clean_value(val):
        """تنظيف القيمة من القيم الفارغة"""
        if val is None:
            return None
        if isinstance(val, str):
            val_lower = val.lower().strip()
            if val_lower in ['null', 'none', '', 'n/a', 'na', '-']:
                return None
        return val
    
    @staticmethod
    def update_from_ai_result(context: ConversationContext, ai_result: Dict, message: str = ""):
        """
        تحديث البيانات المستخرجة من AI مع fallback للاستخراج اليدوي
        🆕 يدمج البيانات الجديدة مع القديمة بدلاً من استبدالها
        
        Args:
            context: سياق المحادثة
            ai_result: نتيجة تحليل AI
            message: الرسالة الأصلية
        """
        # 🆕 حفظ البيانات القديمة للدمج
        old_vehicle = context.vehicle_data.copy()
        old_profile = context.profile_data.copy()
        
        # بيانات السيارة من AI - دمج مع القديمة (مع تنظيف القيم)
        brand = DataExtractor._clean_value(ai_result.get('extracted_vehicle_brand'))
        if brand:
            context.vehicle_data['brand'] = brand
        
        model = DataExtractor._clean_value(ai_result.get('extracted_vehicle_model'))
        if model:
            context.vehicle_data['model'] = model
        
        year = ai_result.get('extracted_vehicle_year')
        if year and year > 0:
            context.vehicle_data['year'] = year
        
        value = ai_result.get('extracted_vehicle_value')
        if value and value > 0:
            context.vehicle_data['value'] = value
        
        plate_no = DataExtractor._clean_value(ai_result.get('extracted_plate_number'))
        if plate_no:
            context.vehicle_data['plate_no'] = plate_no
        
        service_type = DataExtractor._clean_value(ai_result.get('extracted_service_type'))
        if service_type:
            context.vehicle_data['service_type'] = service_type
        
        # بيانات العميل من AI - دمج مع القديمة (مع تنظيف القيم)
        national_id = DataExtractor._clean_value(ai_result.get('extracted_national_id'))
        if national_id:
            context.profile_data['national_id'] = national_id
        
        birth_date = DataExtractor._clean_value(ai_result.get('extracted_birth_date'))
        if birth_date:
            context.profile_data['birth_date'] = birth_date
        
        # Fallback: استخراج يدوي من النص إذا لم يستخرج AI
        if message:
            DataExtractor.fallback_extract(context, message)
        
        # 🆕 التأكد من الاحتفاظ بالبيانات القديمة إذا لم تُستبدل
        for key, value in old_vehicle.items():
            if key not in context.vehicle_data or not context.vehicle_data[key]:
                if DataExtractor._clean_value(value):
                    context.vehicle_data[key] = value
        
        for key, value in old_profile.items():
            if key not in context.profile_data or not context.profile_data[key]:
                if DataExtractor._clean_value(value):
                    context.profile_data[key] = value
        
        # تنظيف القيم الفارغة من البيانات
        context.vehicle_data = {k: v for k, v in context.vehicle_data.items() if DataExtractor._clean_value(v) is not None}
        context.profile_data = {k: v for k, v in context.profile_data.items() if DataExtractor._clean_value(v) is not None}
        
        # Log للتأكد من حفظ البيانات
        logger.info(f"📝 Updated vehicle_data: {context.vehicle_data}")
        logger.info(f"📝 Updated profile_data: {context.profile_data}")
    
    @staticmethod
    def fallback_extract(context: ConversationContext, message: str):
        """
        استخراج يدوي للبيانات كـ fallback
        
        Args:
            context: سياق المحادثة
            message: الرسالة
        """
        # استخراج السنة
        if not context.vehicle_data.get('year'):
            year_match = re.search(YEAR_PATTERN, message)
            if year_match:
                context.vehicle_data['year'] = int(year_match.group())
        
        # استخراج القيمة
        if not context.vehicle_data.get('value'):
            for pattern in VALUE_PATTERNS:
                value_match = re.search(pattern, message)
                if value_match:
                    val_str = value_match.group(1).replace(',', '')
                    val = int(val_str)
                    # تجنب السنوات (1990-2030) والهويات (10 أرقام)
                    if 15000 <= val <= 2000000 and len(val_str) != 10:
                        context.vehicle_data['value'] = val
                        break
        
        # استخراج رقم اللوحة
        if not context.vehicle_data.get('plate_no'):
            for pattern in PLATE_PATTERNS:
                plate_match = re.search(pattern, message)
                if plate_match:
                    plate = plate_match.group(1).strip()
                    # تحقق من أن اللوحة ليست رقم هوية أو سنة
                    if len(plate) >= 4:
                        # تجنب الأرقام فقط (قد تكون سنة أو قيمة)
                        if not plate.replace(' ', '').isdigit():
                            context.vehicle_data['plate_no'] = plate
                            logger.debug(f"📝 Extracted plate: {plate}")
                            break
        
        # استخراج رقم الهوية
        if not context.profile_data.get('national_id'):
            id_match = re.search(NATIONAL_ID_PATTERN, message)
            if id_match:
                national_id = id_match.group(1)
                # تحقق إضافي: ليست سنة أو قيمة سيارة
                if not (1990 <= int(national_id[:4]) <= 2030):
                    context.profile_data['national_id'] = national_id
        
        # استخراج تاريخ الميلاد
        if not context.profile_data.get('birth_date'):
            for pattern in DATE_PATTERNS:
                date_match = re.search(pattern, message)
                if date_match:
                    date_str = date_match.group(1).replace('/', '-')
                    context.profile_data['birth_date'] = date_str
                    break
        
        # الماركات الشائعة
        if not context.vehicle_data.get('brand'):
            msg_lower = message.lower()
            for key, val in BRAND_MAPPING.items():
                if key in msg_lower or key in message:
                    context.vehicle_data['brand'] = val
                    break
        
        # الموديلات الشائعة
        if not context.vehicle_data.get('model'):
            msg_lower = message.lower()
            for key, val in MODEL_MAPPING.items():
                if key in msg_lower or key in message:
                    context.vehicle_data['model'] = val
                    break
        
        # نوع التأمين
        if not context.vehicle_data.get('service_type'):
            msg_lower = message.lower()
            for service_type, keywords in SERVICE_TYPE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in msg_lower or keyword in message:
                        context.vehicle_data['service_type'] = service_type
                        break
                if context.vehicle_data.get('service_type'):
                    break
    
    @staticmethod
    def is_vehicle_data_complete(context: ConversationContext) -> bool:
        """
        التحقق من اكتمال بيانات السيارة
        
        Args:
            context: سياق المحادثة
        
        Returns:
            bool: هل البيانات مكتملة
        """
        v = context.vehicle_data
        return all([
            v.get('brand'),
            v.get('model'),
            v.get('year'),
            v.get('value'),
            v.get('plate_no')
        ])
    
    @staticmethod
    def is_profile_data_complete(context: ConversationContext) -> bool:
        """
        التحقق من اكتمال بيانات العميل
        
        Args:
            context: سياق المحادثة
        
        Returns:
            bool: هل البيانات مكتملة
        """
        p = context.profile_data
        return all([
            p.get('national_id'),
            p.get('birth_date')
        ])
