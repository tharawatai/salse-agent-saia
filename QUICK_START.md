# 🚀 دليل البدء السريع - SAIA Django Project

## المتطلبات الأساسية

- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (اختياري للـ caching)

## خطوات التشغيل السريعة

### 1. إعداد البيئة

```powershell
# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة
.\venv\Scripts\activate

# ترقية pip
python -m pip install --upgrade pip

# تثبيت المكتبات
pip install -r requirements.txt
```

### 2. إعداد قاعدة البيانات

```powershell
# إنشاء قاعدة بيانات PostgreSQL
# افتح psql أو pgAdmin وقم بتنفيذ:
# CREATE DATABASE saia_insurance;
# CREATE USER saia_user WITH PASSWORD 'your_password';
# GRANT ALL PRIVILEGES ON DATABASE saia_insurance TO saia_user;
```

### 3. إعداد ملف .env

```powershell
# نسخ ملف المثال
copy .env.example .env

# تعديل القيم في .env
# افتح .env وعدل:
# - SECRET_KEY
# - DB_PASSWORD
# - GOOGLE_API_KEY (إن وجد)
```

### 4. تطبيق Migrations

```powershell
# إنشاء migrations
python manage.py makemigrations

# تطبيق migrations
python manage.py migrate

# إنشاء superuser
python manage.py createsuperuser
```

### 5. تشغيل السيرفر

```powershell
# تشغيل السيرفر
python manage.py runserver

# افتح المتصفح على:
# http://127.0.0.1:8000/admin/
```

### 6. اختبار Models

```powershell
# تشغيل سكريبت الاختبار
python scripts/test_models.py
```

## الخطوات التالية

1. ✅ إضافة بيانات تجريبية من Admin Panel
2. ✅ اختبار AI Assistants
3. ✅ إعداد WhatsApp Integration (اختياري)
4. ✅ إعداد Payment Gateways (اختياري)

## المشاكل الشائعة

### خطأ في الاتصال بقاعدة البيانات
```powershell
# تأكد من تشغيل PostgreSQL
# تأكد من صحة بيانات الاتصال في .env
```

### خطأ في استيراد المكتبات
```powershell
# تأكد من تفعيل البيئة الافتراضية
.\venv\Scripts\activate

# أعد تثبيت المكتبات
pip install -r requirements.txt
```

## الدعم

راجع الملفات التالية للمزيد من المعلومات:
- `README.md` - معلومات عامة
- `CHECKLIST.md` - قائمة تحقق شاملة
- `START_HERE.md` - دليل مفصل

---

**تم إنشاؤه بواسطة Kiro AI Assistant**
