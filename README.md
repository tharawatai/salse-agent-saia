# 🚀 SAIA Insurance System

<div dir="rtl">

نظام تأمين ذكي متكامل مع مساعدين AI وتكامل WhatsApp Business

</div>

## ✨ المميزات

- 🤖 **6 مساعدين AI متخصصين** - باستخدام Google Gemini
- 💬 **تكامل كامل مع WhatsApp Business** - محادثات تلقائية ذكية
- 💳 **دعم بوابات الدفع السعودية** - Moyasar و HyperPay
- 📊 **لوحة تحكم احترافية** - Django Admin مخصصة
- 🔒 **نظام أمان متقدم** - مصادقة وصلاحيات
- 📱 **واجهة عربية كاملة** - دعم كامل للغة العربية

## 🏗️ البنية المعمارية

```
SAIA_PROJECT/
├── insurance_core/      # النماذج الأساسية (9 Models)
├── insurance_ai/        # المساعدين الذكيين (6 Assistants)
├── whatsapp_integration/# تكامل WhatsApp
├── payments/            # بوابات الدفع
└── saia_insurance/      # إعدادات المشروع
```

## 🛠️ التقنيات المستخدمة

- **Backend**: Django 5.0
- **AI**: LangChain + Google Gemini
- **Database**: SQLite (تطوير) / PostgreSQL (إنتاج)
- **Cache**: LocMemCache (تطوير) / Redis (إنتاج)
- **Tasks**: Celery (اختياري)
- **Deployment**: Docker + Docker Compose

## 📦 التثبيت السريع

### المتطلبات
- Python 3.13+
- pip
- Docker (لـ PostgreSQL)

### الخطوات

#### 1. إنشاء البيئة الافتراضية
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 2. تثبيت المكتبات
```powershell
pip install -r requirements.txt
```

#### 3. تشغيل PostgreSQL (Docker)
```powershell
docker-compose up -d db
```

#### 4. إعداد البيئة
```powershell
# نسخ ملف البيئة
Copy-Item .env.example .env

# تعديل .env وإضافة:
# GEMINI_API_KEY=your-gemini-api-key
```

#### 5. تطبيق Migrations
```powershell
python manage.py migrate
```

#### 6. إنشاء حساب المدير
```powershell
python scripts/create_superuser.py
```

#### 7. إضافة بيانات تجريبية
```powershell
python scripts/add_sample_data.py
```

#### 8. تشغيل الخادم
```powershell
python manage.py runserver
```

### 🎯 البدء السريع (سكريبت واحد)
```powershell
.\quick_start.ps1
```

## 🗄️ قاعدة البيانات

### PostgreSQL (الافتراضي - موصى به)
```yaml
# docker-compose.yml
db:
  image: postgres:15
  ports: "5433:5432"
  environment:
    POSTGRES_DB: saia_insurance
    POSTGRES_USER: saia_user
    POSTGRES_PASSWORD: saia_password_2025
```

### SQLite (للتطوير السريع فقط)
أضف في `.env`:
```
USE_SQLITE=True
```

## 🔐 معلومات تسجيل الدخول

- **URL**: http://127.0.0.1:8000/admin/
- **اسم المستخدم**: `admin`
- **كلمة المرور**: `admin123`

## 📊 Models الأساسية

### 1. User
نموذج مستخدم مخصص مع معلومات إضافية

### 2. Vehicle
معلومات المركبات

### 3. InsuranceCompany
شركات التأمين (5 شركات)

### 4. InsuranceService
خدمات التأمين (3 خدمات)

### 5. InsuranceOffer
عروض التأمين (16 عرض)

### 6. InsuranceOrder
طلبات التأمين

### 7. Invoice
الفواتير

### 8. Payment
المدفوعات

### 9. Policy
وثائق التأمين

## 🤖 AI Assistants

### 1. InsuranceMainAssistant
المنسق الرئيسي - يوجه المستخدم للمساعد المناسب

### 2. ProfileCollectorAssistant
جمع البيانات الشخصية

### 3. VehicleCollectorAssistant
جمع بيانات المركبة

### 4. OfferSearchAssistant
البحث عن العروض

### 5. OrderProcessorAssistant
معالجة الطلبات

### 6. PaymentAssistant
إدارة الدفع

## 🧪 الاختبارات

### اختبار Models
```powershell
python scripts/test_models.py
```
**النتيجة**: ✅ نجح 100%

### اختبار AI Assistants (يحتاج تفعيل)
```powershell
python scripts/test_ai_assistants.py
```

### اختبار النظام الكامل (يحتاج تفعيل)
```powershell
python scripts/test_full_system.py
```

## 📚 الوثائق

- [دليل إضافة Agent جديد](../دليل_إضافة_Agent_جديد.md)
- [تحليل المشروع](../تحليل_المشروع.md)
- [خطة الدمج](../خطة_دمج_SAIA_مع_Django_AI_Assistant.md)
- [تقرير التنفيذ](../تقرير_التنفيذ_النهائي.md)

## 📝 الترخيص

MIT License

## 📞 الدعم

للدعم والاستفسارات: support@saia.com

---

**تم التطوير بواسطة**: SAIA Team  
**الإصدار**: 1.0.0  
**التاريخ**: 2025-01-19
# salse-agent-saia
# salse-agent-saia
