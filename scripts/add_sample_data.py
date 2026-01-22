"""
سكريبت لإضافة بيانات تجريبية
"""
import os
import sys
import django
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saia_insurance.settings.development')
django.setup()

from insurance_core.models import *

print("📦 إضافة بيانات تجريبية...\n")

# 1. شركات التأمين
print("1️⃣ إضافة شركات التأمين...")
companies_data = [
    {'code': 'TAWUNIYA', 'name_ar': 'التعاونية', 'name_en': 'Tawuniya', 'rating': 4.5},
    {'code': 'ALRAJHI', 'name_ar': 'الراجحي', 'name_en': 'AlRajhi Takaful', 'rating': 4.7},
    {'code': 'MEDGULF', 'name_ar': 'ميدغلف', 'name_en': 'MedGulf', 'rating': 4.3},
    {'code': 'SAICO', 'name_ar': 'سايكو', 'name_en': 'SAICO', 'rating': 4.2},
    {'code': 'WALAA', 'name_ar': 'ولاء', 'name_en': 'Walaa', 'rating': 4.4},
]

companies = []
for data in companies_data:
    company, created = InsuranceCompany.objects.get_or_create(
        company_code=data['code'],
        defaults={
            'name_ar': data['name_ar'],
            'name_en': data['name_en'],
            'rating_score': data['rating']
        }
    )
    companies.append(company)
    print(f"   {'✅ أضيف' if created else '⏭️ موجود'}: {company.name_ar}")

# 2. الخدمات
print("\n2️⃣ إضافة الخدمات...")
services_data = [
    {'code': 'AUTO_COMP', 'name_ar': 'تأمين شامل', 'name_en': 'Comprehensive', 'type': 'AUTO_COMP'},
    {'code': 'AUTO_TPL', 'name_ar': 'تأمين ضد الغير', 'name_en': 'Third Party', 'type': 'AUTO_TPL'},
    {'code': 'AUTO_COMP_PLUS', 'name_ar': 'تأمين شامل بلس', 'name_en': 'Comprehensive Plus', 'type': 'AUTO_COMP'},
]

services = []
for data in services_data:
    service, created = InsuranceService.objects.get_or_create(
        service_code=data['code'],
        defaults={
            'name_ar': data['name_ar'],
            'name_en': data['name_en'],
            'service_type': data['type']
        }
    )
    services.append(service)
    print(f"   {'✅ أضيف' if created else '⏭️ موجود'}: {service.name_ar}")

# 3. العروض
print("\n3️⃣ إضافة العروض...")
offers_count = 0
for company in companies:
    for service in services:
        # تأمين شامل
        if service.service_type == 'AUTO_COMP':
            offer, created = InsuranceOffer.objects.get_or_create(
                company=company,
                service=service,
                offer_code=f'{company.company_code}_{service.service_code}',
                defaults={
                    'coverage_type': 'comprehensive',
                    'price_base': 3000 + (companies.index(company) * 200),
                    'min_age': 18,
                    'max_age': 70,
                    'min_vehicle_year': 2010,
                    'included_features_json': [
                        'تغطية شاملة',
                        'مساعدة على الطريق',
                        'سيارة بديلة'
                    ]
                }
            )
            if created:
                offers_count += 1
        
        # تأمين ضد الغير
        elif service.service_type == 'AUTO_TPL':
            offer, created = InsuranceOffer.objects.get_or_create(
                company=company,
                service=service,
                offer_code=f'{company.company_code}_{service.service_code}',
                defaults={
                    'coverage_type': 'third_party',
                    'price_base': 500 + (companies.index(company) * 50),
                    'min_age': 18,
                    'max_age': 75,
                    'min_vehicle_year': 2000,
                    'included_features_json': [
                        'تغطية ضد الغير',
                        'حد أدنى للتغطية'
                    ]
                }
            )
            if created:
                offers_count += 1

print(f"   ✅ تم إضافة {offers_count} عرض جديد")

# 4. مستخدمين تجريبيين
print("\n4️⃣ إضافة مستخدمين تجريبيين...")
users_data = [
    {'username': '0501111111', 'national_id': '1011111111', 'first_name': 'أحمد', 'last_name': 'محمد', 'city': 'الرياض'},
    {'username': '0502222222', 'national_id': '1022222222', 'first_name': 'محمد', 'last_name': 'علي', 'city': 'جدة'},
    {'username': '0503333333', 'national_id': '1033333333', 'first_name': 'خالد', 'last_name': 'سعيد', 'city': 'الدمام'},
]

users = []
for data in users_data:
    user, created = User.objects.get_or_create(
        username=data['username'],
        defaults={
            'national_id': data['national_id'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'birth_date': date(1990, 1, 1),
            'phone': data['username'],
            'city': data['city'],
            'email': f"{data['username']}@example.com"
        }
    )
    users.append(user)
    print(f"   {'✅ أضيف' if created else '⏭️ موجود'}: {user.get_full_name()}")

# 5. مركبات تجريبية
print("\n5️⃣ إضافة مركبات تجريبية...")
vehicles_data = [
    {'user': users[0], 'plate': 'ABC1234', 'brand': 'تويوتا', 'model': 'كامري', 'year': 2020, 'value': 80000},
    {'user': users[1], 'plate': 'XYZ5678', 'brand': 'هيونداي', 'model': 'سوناتا', 'year': 2019, 'value': 70000},
    {'user': users[2], 'plate': 'DEF9012', 'brand': 'نيسان', 'model': 'التيما', 'year': 2021, 'value': 90000},
]

vehicles = []
for data in vehicles_data:
    vehicle, created = Vehicle.objects.get_or_create(
        plate_no=data['plate'],
        defaults={
            'user': data['user'],
            'brand': data['brand'],
            'model': data['model'],
            'model_year': data['year'],
            'vehicle_value': data['value']
        }
    )
    vehicles.append(vehicle)
    print(f"   {'✅ أضيف' if created else '⏭️ موجود'}: {vehicle.brand} {vehicle.model} - {vehicle.plate_no}")

print("\n✨ تم إضافة جميع البيانات التجريبية بنجاح!")
print(f"\n📊 الإحصائيات:")
print(f"   شركات التأمين: {InsuranceCompany.objects.count()}")
print(f"   الخدمات: {InsuranceService.objects.count()}")
print(f"   العروض: {InsuranceOffer.objects.count()}")
print(f"   المستخدمون: {User.objects.count()}")
print(f"   المركبات: {Vehicle.objects.count()}")
