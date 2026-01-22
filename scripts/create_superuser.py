"""
سكريبت لإنشاء superuser
"""
import os
import sys
import django
from datetime import date

# إضافة المسار للمشروع
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saia_insurance.settings.development')
django.setup()

from insurance_core.models import User

print("🔐 إنشاء حساب مدير النظام...\n")

# حذف المستخدم إذا كان موجوداً
User.objects.filter(username='admin').delete()

# إنشاء superuser
admin = User.objects.create_superuser(
    username='admin',
    national_id='1111111111',
    email='admin@saia.com',
    password='admin123',
    first_name='Admin',
    last_name='User',
    birth_date=date(1990, 1, 1),
    phone='0500000000',
    city='الرياض'
)

print(f"✅ تم إنشاء حساب المدير بنجاح!")
print(f"   اسم المستخدم: admin")
print(f"   كلمة المرور: admin123")
print(f"   البريد: admin@saia.com")
print(f"\n🌐 يمكنك الآن تسجيل الدخول إلى لوحة التحكم:")
print(f"   python manage.py runserver")
print(f"   ثم افتح: http://127.0.0.1:8000/admin/")
