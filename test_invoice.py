"""
اختبار توليد الفاتورة
"""
import os
import sys
from datetime import datetime

# إضافة المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saia_insurance.settings')

import django
django.setup()

from insurance_ai.pdf_generator import pdf_generator

# بيانات اختبار
test_data = {
    'invoice_id': f'INV-{datetime.now().strftime("%H%M%S")}',
    'national_id': '1234567890',
    'birth_date': '1990-05-15',
    'phone': '0501234567',
    'total_amount': 3312.00,
    'coverage_type': 'تأمين شامل',
    'vehicle_brand': 'تويوتا',
    'vehicle_model': 'كامري',
    'vehicle_year': '2024',
    'plate_no': 'أ ب ج 1234',
    'company_name': 'الراجحي للتأمين',
}

print("🧪 اختبار توليد الفاتورة...")
print("="*50)

# توليد الفاتورة
result = pdf_generator.save_invoice_html(test_data)

print(f"📄 الملف: {result}")
print(f"✅ تم التوليد بنجاح!")

# فتح الملف
if os.path.exists(result):
    print(f"📂 حجم الملف: {os.path.getsize(result)} bytes")
    
    # عرض أول 500 حرف من HTML إذا كان HTML
    if result.endswith('.html'):
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"\n📝 محتوى HTML (أول 500 حرف):")
            print(content[:500])
