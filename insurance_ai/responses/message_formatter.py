"""
MessageFormatter - تنسيق الرسائل لتكون متوافقة مع جميع المنصات
يدعم: واتساب، ويب، تيليجرام، وغيرها
"""
from typing import List, Dict, Any


class MessageFormatter:
    """منسق الرسائل للتوافق مع جميع المنصات"""
    
    # رموز بسيطة تعمل في كل مكان
    CHECK = "✅"
    CROSS = "❌"
    BULLET = "•"
    ARROW = "→"
    STAR = "⭐"
    CAR = "🚗"
    MONEY = "💰"
    PERCENT = "🏷️"
    DOC = "📋"
    USER = "👤"
    PHONE = "📱"
    ID = "🆔"
    DATE = "📅"
    COMPANY = "🏢"
    EDIT = "✏️"
    CANCEL = "❌"
    BACK = "⬅️"
    PROGRESS = "📊"
    TIME = "⏳"
    CELEBRATE = "🎉"
    WARNING = "⚠️"
    INFO = "ℹ️"
    
    @staticmethod
    def header(title: str) -> str:
        """عنوان رئيسي"""
        line = "─" * 30
        return f"{line}\n{title}\n{line}"
    
    @staticmethod
    def subheader(title: str) -> str:
        """عنوان فرعي"""
        return f"\n▸ {title}\n"
    
    @staticmethod
    def separator() -> str:
        """فاصل"""
        return "─" * 30
    
    @staticmethod
    def progress_bar(completed: int, total: int) -> str:
        """شريط تقدم بسيط"""
        filled = "●" * completed
        empty = "○" * (total - completed)
        return f"[{filled}{empty}] {completed}/{total}"
    
    @staticmethod
    def field_status(name: str, value: Any, has_value: bool = None) -> str:
        """حقل مع حالته"""
        if has_value is None:
            has_value = bool(value) and value != '---'
        
        status = MessageFormatter.CHECK if has_value else MessageFormatter.CROSS
        display_value = value if has_value else "---"
        return f"{status} {name}: {display_value}"
    
    @staticmethod
    def bullet_list(items: List[str]) -> str:
        """قائمة نقطية"""
        return "\n".join([f"{MessageFormatter.BULLET} {item}" for item in items])
    
    @staticmethod
    def numbered_list(items: List[str]) -> str:
        """قائمة مرقمة"""
        return "\n".join([f"{i}. {item}" for i, item in enumerate(items, 1)])
    
    @staticmethod
    def price_line(label: str, amount: float, prefix: str = "") -> str:
        """سطر سعر"""
        return f"{prefix}{label}: {amount:,.0f} ريال"
    
    @staticmethod
    def format_offer_simple(offer: Dict, num: int) -> str:
        """تنسيق عرض بسيط للواتساب"""
        company = offer.get('company', '')
        rating = offer.get('company_rating', 0)
        base_price = offer.get('base_price', 0)
        discount = offer.get('discount', 0)
        price_after = offer.get('price_after_discount', base_price - discount)
        vat = offer.get('vat', 0)
        final_price = offer.get('final_price', 0)
        coverage = offer.get('coverage_type', 'شامل')
        
        stars = "⭐" * int(rating)
        
        return f"""
*العرض {num}* - {company}
{stars} ({rating}/5)
📑 التغطية: {coverage}

💰 السعر: {base_price:,.0f} ريال
🏷️ الخصم: -{discount:,.0f} ريال
💵 بعد الخصم: {price_after:,.0f} ريال
📊 الضريبة: +{vat:,.0f} ريال
━━━━━━━━━━━━━━━
💎 *الإجمالي: {final_price:,.0f} ريال*
"""
    
    @staticmethod
    def format_vehicle_status(vehicle_data: Dict) -> str:
        """تنسيق حالة بيانات السيارة - احترافي"""
        v = vehicle_data
        
        # تحديد حالة كل حقل
        brand = v.get('brand')
        model = v.get('model')
        year = v.get('year')
        value = v.get('value')
        plate_no = v.get('plate_no')
        
        # حساب التقدم
        fields_status = [brand, model, year, value, plate_no]
        completed = sum(1 for f in fields_status if f)
        
        # بناء الرد
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📝 *بيانات السيارة المطلوبة*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        # عرض كل حقل
        def field_line(icon: str, name: str, value: any, format_func=None):
            status = "✅" if value else "❌"
            if value:
                display = format_func(value) if format_func else str(value)
                return f"│ {status} {icon} {name}: *{display}*"
            else:
                return f"│ {status} {icon} {name}: ---"
        
        lines.append("┌─────────────────────────")
        lines.append(field_line("🏭", "الماركة", brand))
        lines.append(field_line("📱", "الموديل", model))
        lines.append(field_line("📅", "سنة الصنع", year))
        lines.append(field_line("💰", "القيمة", value, lambda x: f"{x:,.0f} ريال"))
        lines.append(field_line("🔢", "رقم اللوحة", plate_no))
        lines.append("└─────────────────────────")
        
        lines.append("")
        
        # شريط التقدم
        progress_filled = "●" * completed
        progress_empty = "○" * (5 - completed)
        percentage = int((completed / 5) * 100)
        lines.append(f"📊 التقدم: [{progress_filled}{progress_empty}] {percentage}%")
        
        if completed < 5:
            missing = []
            if not brand: missing.append("الماركة")
            if not model: missing.append("الموديل")
            if not year: missing.append("السنة")
            if not value: missing.append("القيمة")
            if not plate_no: missing.append("اللوحة")
            lines.append(f"⏳ المتبقي: {', '.join(missing)}")
            lines.append("")
            lines.append("💡 *مثال:* تويوتا كامري 2024 قيمتها 100000 لوحة أ ب ج 1234")
        else:
            lines.append("✅ جميع البيانات مكتملة!")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_profile_status(profile_data: Dict) -> str:
        """تنسيق حالة البيانات الشخصية - احترافي"""
        p = profile_data
        
        national_id = p.get('national_id')
        birth_date = p.get('birth_date')
        
        completed = sum(1 for f in [national_id, birth_date] if f)
        
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "� *البيانات الشخصية المطلوبة*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        # عرض كل حقل
        lines.append("┌─────────────────────────")
        
        status_id = "✅" if national_id else "❌"
        display_id = f"*{national_id}*" if national_id else "---"
        lines.append(f"│ {status_id} 🆔 رقم الهوية: {display_id}")
        
        status_date = "✅" if birth_date else "❌"
        display_date = f"*{birth_date}*" if birth_date else "---"
        lines.append(f"│ {status_date} 📅 تاريخ الميلاد: {display_date}")
        
        lines.append("└─────────────────────────")
        lines.append("")
        
        # شريط التقدم
        progress_filled = "●" * completed
        progress_empty = "○" * (2 - completed)
        percentage = int((completed / 2) * 100)
        lines.append(f"📊 التقدم: [{progress_filled}{progress_empty}] {percentage}%")
        
        if completed < 2:
            missing = []
            if not national_id: missing.append("رقم الهوية (10 أرقام)")
            if not birth_date: missing.append("تاريخ الميلاد")
            lines.append(f"⏳ المتبقي: {', '.join(missing)}")
            lines.append("")
            lines.append("💡 *مثال:* 1234567890 1990-01-15")
        else:
            lines.append("✅ جميع البيانات مكتملة!")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_services_list(services: List[Dict]) -> str:
        """تنسيق قائمة الخدمات"""
        lines = [
            "🚗 *خدمات SAIA للتأمين*",
            ""
        ]
        
        for i, service in enumerate(services, 1):
            name = service.get('name_ar', '')
            desc = service.get('description', '')
            service_type = service.get('service_type', '')
            
            icon = "🛡️" if 'شامل' in name or 'COMP' in service_type else "🚗"
            
            lines.append(f"{icon} *{i}. {name}*")
            if desc:
                lines.append(f"   {desc[:100]}")
            lines.append("")
        
        lines.extend([
            "✨ *مميزاتنا:*",
            "✅ أسعار تنافسية مع خصم نجم",
            "✅ شركات تأمين موثوقة",
            "✅ إصدار فوري للوثائق",
            "✅ دعم على مدار الساعة",
            "",
            "💬 ما نوع التأمين الذي تريده؟"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_offers_list(offers: List[Dict]) -> str:
        """تنسيق قائمة العروض"""
        if not offers:
            return "عذراً، لم نجد عروضاً متاحة حالياً."
        
        lines = [
            "🚗 *العروض المتاحة لتأمين سيارتك*",
            ""
        ]
        
        for i, offer in enumerate(offers, 1):
            lines.append(MessageFormatter.format_offer_simple(offer, i))
        
        lines.extend([
            "",
            "💡 لاختيار عرض، أرسل رقمه (1 أو 2 أو 3...)",
            "❓ لمعرفة تفاصيل أكثر، اختر العرض أولاً"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def format_vehicle_confirmation(vehicle_data: Dict) -> str:
        """تنسيق تأكيد بيانات السيارة - احترافي"""
        v = vehicle_data
        
        brand = v.get('brand', '---')
        model = v.get('model', '---')
        year = v.get('year', '---')
        value = v.get('value', 0)
        plate_no = v.get('plate_no', '---')
        service_type = v.get('service_type', 'comprehensive')
        
        # تحديد نوع التأمين
        if service_type == 'comprehensive':
            insurance_type = 'تأمين شامل'
            insurance_icon = '🛡️'
        elif service_type == 'tpl':
            insurance_type = 'تأمين ضد الغير'
            insurance_icon = '🚗'
        elif service_type == 'comprehensive_plus':
            insurance_type = 'تأمين شامل بلس'
            insurance_icon = '💎'
        else:
            insurance_type = 'تأمين شامل'
            insurance_icon = '🛡️'
        
        # تنسيق القيمة
        value_formatted = f"{value:,.0f}" if value else "---"
        
        return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *بيانات سيارتك*
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚗 *معلومات السيارة:*
┌─────────────────────────
│ 🏭 الماركة: *{brand}*
│ 📱 الموديل: *{model}*
│ 📅 سنة الصنع: *{year}*
│ 💰 القيمة: *{value_formatted} ريال*
│ 🔢 رقم اللوحة: *{plate_no}*
└─────────────────────────

{insurance_icon} *نوع التأمين:* {insurance_type}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ هل هذه البيانات صحيحة؟
━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    @staticmethod
    def format_profile_confirmation(profile_data: Dict, phone: str = None) -> str:
        """تنسيق تأكيد البيانات الشخصية - احترافي"""
        p = profile_data
        
        national_id = p.get('national_id', '---')
        birth_date = p.get('birth_date', '---')
        phone_num = p.get('phone', phone or '---')
        
        return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 *بياناتك الشخصية*
━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────
│ 🆔 رقم الهوية: *{national_id}*
│ 📅 تاريخ الميلاد: *{birth_date}*
│ 📱 رقم الجوال: *{phone_num}*
└─────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ هل هذه البيانات صحيحة؟
━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    @staticmethod
    def format_order_summary(vehicle_data: Dict, profile_data: Dict, offer: Dict) -> str:
        """تنسيق ملخص الطلب - احترافي"""
        v = vehicle_data
        p = profile_data
        
        company = offer.get('company', '')
        if isinstance(company, dict):
            company = company.get('name_ar', '')
        
        base_price = offer.get('base_price', 0)
        discount = offer.get('discount', 0)
        vat = offer.get('vat', 0)
        final_price = offer.get('final_price', 0)
        
        service_type = v.get('service_type', 'comprehensive')
        if service_type == 'comprehensive':
            insurance_type = 'تأمين شامل'
        elif service_type == 'tpl':
            insurance_type = 'تأمين ضد الغير'
        elif service_type == 'comprehensive_plus':
            insurance_type = 'تأمين شامل بلس'
        else:
            insurance_type = 'تأمين شامل'
        
        coverage = offer.get('coverage_type', insurance_type)
        
        return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *ملخص طلب التأمين*
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚗 *بيانات السيارة:*
┌─────────────────────────
│ 🏭 الماركة: {v.get('brand', '---')}
│ 📱 الموديل: {v.get('model', '---')}
│ 📅 السنة: {v.get('year', '---')}
│ 💰 القيمة: {v.get('value', 0):,.0f} ريال
│ 🔢 اللوحة: {v.get('plate_no', '---')}
│ 🛡️ نوع التأمين: {insurance_type}
└─────────────────────────

👤 *بيانات العميل:*
┌─────────────────────────
│ 🆔 رقم الهوية: {p.get('national_id', '---')}
│ 📅 تاريخ الميلاد: {p.get('birth_date', '---')}
└─────────────────────────

🏢 *العرض المختار:*
┌─────────────────────────
│ 🏛️ الشركة: {company}
│ 📑 التغطية: {coverage}
└─────────────────────────

💰 *تفاصيل السعر:*
┌─────────────────────────
│ 💵 السعر الأساسي: {base_price:,.0f} ريال
│ 🏷️ الخصم: -{discount:,.0f} ريال
│ 📊 الضريبة (15%): +{vat:,.0f} ريال
├─────────────────────────
│ 💎 *الإجمالي: {final_price:,.0f} ريال*
└─────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ يرجى مراجعة البيانات بعناية
✅ هل تؤكد صحة البيانات وتوافق على إصدار الفاتورة؟
━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    @staticmethod
    def format_offer_details(offer: Dict, num: int) -> str:
        """تنسيق تفاصيل العرض"""
        company = offer.get('company', '')
        if isinstance(company, dict):
            company_name = company.get('name_ar', '')
            rating = company.get('rating', 0)
        else:
            company_name = str(company)
            rating = offer.get('company_rating', 0)
        
        # جلب الأسعار - قد تكون في pricing dict أو مباشرة في offer
        pricing = offer.get('pricing', {})
        base_price = pricing.get('base_price', offer.get('base_price', 0))
        discount = pricing.get('discount', offer.get('discount', 0))
        price_after = pricing.get('price_after_discount', offer.get('price_after_discount', base_price - discount))
        vat = pricing.get('vat', offer.get('vat', 0))
        final_price = pricing.get('final_price', offer.get('final_price', 0))
        
        # جلب المزايا
        features = offer.get('features', offer.get('included_features', offer.get('included_features_json', [])))
        if not features:
            features = ["تغطية شاملة للحوادث", "تغطية السرقة والحريق", "خدمة المساعدة على الطريق"]
        
        features_text = "\n".join([f"✅ {f}" for f in features[:5]])
        
        # نوع التغطية
        coverage = offer.get('coverage_type_display', offer.get('coverage_type', 'شامل'))
        if coverage == 'comprehensive':
            coverage = 'شامل'
        elif coverage == 'tpl':
            coverage = 'ضد الغير'
        
        return f"""📋 *تفاصيل العرض رقم {num}*

🏢 الشركة: {company_name}
⭐ التقييم: {'⭐' * int(rating)} ({rating}/5)
📑 التغطية: {coverage}

💰 *تفصيل السعر:*
• السعر الأساسي: {base_price:,.0f} ريال
• خصم نجم: -{discount:,.0f} ريال
• بعد الخصم: {price_after:,.0f} ريال
• الضريبة (15%): +{vat:,.0f} ريال
━━━━━━━━━━━━━━━
💎 *الإجمالي: {final_price:,.0f} ريال*

🎉 وفرت: {discount:,.0f} ريال

✨ *مزايا التغطية:*
{features_text}

✅ هل تؤكد اختيارك لهذا العرض؟"""
