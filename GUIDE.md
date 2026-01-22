# 🚗 SAIA - دليل تشغيل المشروع
## سايا - المساعد الذكي لشركة كونكورد للتأمين

---

## 📋 نظرة عامة

SAIA هو مساعد ذكي لتأمين السيارات يعمل بالذكاء الاصطناعي (Gemini AI)، مصمم لشركة كونكورد للتأمين ومطور من قبل Bineyes.

### المميزات الرئيسية:
- 🤖 محادثة ذكية باللغة العربية
- 🚗 جمع بيانات السيارة تلقائياً
- 💰 عرض عروض التأمين من شركات متعددة
- 📄 إصدار الفواتير والوثائق
- 📱 دعم WhatsApp
- ⚡ أداء سريع مع نظام Cache

---

## 🚀 التشغيل السريع

### 1. المتطلبات
```
Python 3.11+
PostgreSQL (اختياري - يمكن استخدام SQLite)
```

### 2. إعداد البيئة
```bash
cd SAIA_PROJECT

# إنشاء ملف البيئة
copy .env.example .env

# تعديل .env وإضافة مفتاح Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. إعداد قاعدة البيانات
```bash
python manage.py migrate
python manage.py createsuperuser
python scripts/add_sample_data.py
```

### 5. تشغيل السيرفر
```bash
python manage.py runserver 8000
```

### 6. فتح التطبيق
```
http://127.0.0.1:8000/chat/v2/
```

---

## 📁 هيكل المشروع

```
SAIA_PROJECT/
├── insurance_ai/          # التطبيق الرئيسي للذكاء الاصطناعي
│   ├── ai/               # محرك Gemini والـ Prompts
│   │   ├── gemini_engine.py
│   │   └── prompts.py
│   ├── engine/           # محرك المحادثة
│   │   ├── sales_agent.py
│   │   └── modification_handler.py
│   ├── extraction/       # استخراج البيانات
│   ├── responses/        # تنسيق الردود
│   ├── database/         # التعامل مع قاعدة البيانات
│   ├── context/          # إدارة السياق والجلسات
│   ├── api/              # API endpoints
│   └── cache_manager.py  # إدارة الكاش
├── insurance_core/        # النماذج الأساسية
├── whatsapp_integration/  # تكامل واتساب
├── payments/             # نظام الدفع
├── templates/            # قوالب HTML
└── static/               # الملفات الثابتة
```

---

## 🔧 الإعدادات

### ملف .env
```env
# Gemini AI
GEMINI_API_KEY=your_key_here

# قاعدة البيانات (اختياري)
DATABASE_URL=postgres://user:pass@localhost:5432/saia_db

# الإعدادات
DEBUG=True
SECRET_KEY=your_secret_key
```

### إعدادات Django
- Development: `saia_insurance/settings/development.py`
- Production: `saia_insurance/settings/production.py`

---

## 🌐 الواجهات

### 1. واجهة الشات الرئيسية
```
http://127.0.0.1:8000/chat/v2/
```

### 2. لوحة الإدارة
```
http://127.0.0.1:8000/admin/
المستخدم: admin
كلمة المرور: admin123
```

### 3. API Endpoints
```
POST /api/ai/chat/              # إرسال رسالة
GET  /api/ai/invoices/{id}/pdf/ # تحميل فاتورة
GET  /api/ai/policies/{id}/pdf/ # تحميل وثيقة
```

---

## 💬 تدفق المحادثة

```
1. greeting          → الترحيب
2. service_details   → اختيار نوع التأمين
3. collecting_vehicle → جمع بيانات السيارة
4. confirming_vehicle → تأكيد البيانات
5. showing_offers    → عرض العروض
6. offer_details     → تفاصيل العرض
7. collecting_profile → البيانات الشخصية
8. confirming_profile → تأكيد البيانات
9. order_summary     → ملخص الطلب
10. payment_pending  → انتظار الدفع
11. completed        → اكتمال
```

---

## 🧪 الاختبار

### اختبار الشات
```bash
python test_chat_scenario.py
```

### اختبار الاتصال
```bash
python test_frontend_connection.py
```

### اختبار الفاتورة
```bash
python test_invoice.py
```

---

## 📱 تكامل WhatsApp

### إعداد Webhook
1. أضف في `.env`:
```env
WHATSAPP_TOKEN=your_token
WHATSAPP_PHONE_ID=your_phone_id
WHATSAPP_VERIFY_TOKEN=your_verify_token
```

2. Webhook URL:
```
https://your-domain.com/api/whatsapp/webhook/
```

---

## 🐳 Docker

### تشغيل بـ Docker Compose
```bash
docker-compose up -d
```

### الخدمات:
- `web`: Django application (port 8000)
- `db`: PostgreSQL (port 5433)
- `redis`: Redis cache (port 6379)

---

## 📊 لوحة الإدارة

### إدارة البيانات:
- **شركات التأمين**: إضافة/تعديل الشركات
- **العروض**: إدارة عروض التأمين
- **الطلبات**: متابعة الطلبات
- **الفواتير**: عرض الفواتير
- **الوثائق**: إدارة وثائق التأمين

---

## ⚡ تحسين الأداء

### نظام الكاش
- يستخدم Cache First Strategy
- يقلل عمليات قاعدة البيانات بنسبة ~80%
- متوسط وقت الاستجابة: ~2 ثانية

### المراحل التي تحفظ في DB:
- `confirming_vehicle`
- `confirming_profile`
- `payment_pending`
- `completed`

---

## 🔒 الأمان

### في Production:
1. غير `DEBUG=False`
2. استخدم `SECRET_KEY` قوي
3. فعّل HTTPS
4. أضف `ALLOWED_HOSTS`

---

## 📞 الدعم

- **الشركة**: Bineyes Technology
- **المنتج**: SAIA - Smart AI Insurance Assistant
- **العميل**: كونكورد للتأمين

---

## 📝 الأوامر المفيدة

```bash
# تشغيل السيرفر
python manage.py runserver 8000

# إنشاء migrations
python manage.py makemigrations

# تطبيق migrations
python manage.py migrate

# إنشاء مستخدم admin
python manage.py createsuperuser

# إضافة بيانات تجريبية
python scripts/add_sample_data.py

# جمع الملفات الثابتة (للإنتاج)
python manage.py collectstatic
```

---

## 🎯 نصائح

1. **للتطوير**: استخدم SQLite (الافتراضي)
2. **للإنتاج**: استخدم PostgreSQL
3. **للاختبار**: شغل `test_chat_scenario.py`
4. **للفواتير**: افتح HTML في المتصفح واطبع كـ PDF

---

**Powered by SAIA | Bineyes Technology © 2026**
