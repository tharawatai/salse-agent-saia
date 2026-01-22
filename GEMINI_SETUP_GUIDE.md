# 🚀 دليل إعداد Google Gemini AI

## 📋 المتطلبات

1. Python 3.10+
2. Django 5.0+
3. Google Gemini API Key

---

## 🔧 خطوات الإعداد

### 1️⃣ تثبيت المتطلبات

```bash
cd SAIA_PROJECT
pip install -r requirements.txt
```

**المكتبات المطلوبة:**
- `google-generativeai>=0.3.0` - Google Gemini SDK
- `Django>=5.0`
- `djangorestframework>=3.14.0`

---

### 2️⃣ الحصول على Gemini API Key

#### الطريقة 1: من Google AI Studio
1. اذهب إلى: https://makersuite.google.com/app/apikey
2. سجل الدخول بحساب Google
3. اضغط على "Create API Key"
4. انسخ المفتاح

#### الطريقة 2: من Google Cloud Console
1. اذهب إلى: https://console.cloud.google.com/
2. أنشئ مشروع جديد أو اختر مشروع موجود
3. فعّل "Generative Language API"
4. أنشئ API Key من "Credentials"

---

### 3️⃣ إعداد ملف .env

```bash
# نسخ ملف المثال
cp .env.example .env

# تعديل الملف وإضافة المفتاح
nano .env
```

**أضف في .env:**
```env
# AI Configuration
GEMINI_API_KEY=AIzaSy...your-actual-key-here...

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

### 4️⃣ تطبيق Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 5️⃣ إنشاء Superuser (اختياري)

```bash
python manage.py createsuperuser
```

---

### 6️⃣ تشغيل السيرفر

```bash
python manage.py runserver
```

---

## 🧪 الاختبار

### اختبار سريع:

```bash
# PowerShell
.\test_gemini_chat.ps1

# أو Bash
python -c "
import google.generativeai as genai
genai.configure(api_key='YOUR_KEY')
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content('مرحباً')
print(response.text)
"
```

### اختبار API يدوياً:

```bash
curl -X POST http://localhost:8000/api/ai/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "مرحباً، أريد تأمين سيارتي",
    "conversation_id": "test_123"
  }'
```

### اختبار من المتصفح:

افتح: http://localhost:8000/chat/

---

## 📊 التحقق من التثبيت

### 1. التحقق من تثبيت المكتبة:

```python
python -c "import google.generativeai; print('✅ Gemini installed')"
```

### 2. التحقق من صحة API Key:

```python
python manage.py shell

>>> from django.conf import settings
>>> print(settings.GEMINI_API_KEY)
>>> # يجب أن يظهر المفتاح
```

### 3. التحقق من تهيئة AI:

```python
python manage.py shell

>>> from insurance_ai.ai_intent_analyzer import ai_intent_analyzer
>>> print(ai_intent_analyzer.model)
>>> # يجب أن يظهر: GenerativeModel(...)
```

---

## 🔍 استكشاف الأخطاء

### ❌ خطأ: "GEMINI_API_KEY not found"

**الحل:**
```bash
# تأكد من وجود .env في المجلد الصحيح
ls -la .env

# تأكد من تحميل المتغيرات
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GEMINI_API_KEY'))"
```

---

### ❌ خطأ: "API key not valid"

**الحل:**
1. تأكد من نسخ المفتاح كاملاً بدون مسافات
2. تأكد من تفعيل Generative Language API في Google Cloud
3. جرب إنشاء مفتاح جديد

---

### ❌ خطأ: "Resource exhausted"

**الحل:**
- وصلت للحد المجاني (60 requests/minute)
- انتظر دقيقة وحاول مرة أخرى
- أو ترقية للخطة المدفوعة

---

### ❌ خطأ: "Model not found"

**الحل:**
```python
# في professional_engine.py
# تأكد من اسم الموديل الصحيح:
self.model = genai.GenerativeModel('gemini-1.5-flash')  # ✅
# وليس:
self.model = genai.GenerativeModel('gemini-pro')  # ❌ قديم
```

---

## 📝 الموديلات المتاحة

| الموديل | الوصف | السعر |
|---------|-------|-------|
| `gemini-1.5-flash` | سريع ورخيص | مجاني حتى 15 RPM |
| `gemini-1.5-pro` | أقوى وأذكى | مجاني حتى 2 RPM |
| `gemini-1.0-pro` | قديم | مجاني |

**الموصى به:** `gemini-1.5-flash` (سريع وكافي للمحادثات)

---

## 🎯 الاستخدام في الكود

### مثال بسيط:

```python
import google.generativeai as genai
from django.conf import settings

# تهيئة
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# إرسال رسالة
response = model.generate_content("مرحباً")
print(response.text)
```

### مثال مع المحادثة:

```python
# بدء محادثة
chat = model.start_chat(history=[])

# إرسال رسائل
response1 = chat.send_message("ما اسمك؟")
print(response1.text)

response2 = chat.send_message("ما هو عمرك؟")
print(response2.text)
```

### مثال مع إعدادات:

```python
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config=genai.GenerationConfig(
        temperature=0.7,  # 0-1 (أعلى = أكثر إبداعاً)
        max_output_tokens=800,  # الحد الأقصى للرد
        top_p=0.95,
        top_k=40
    )
)
```

---

## 📚 موارد إضافية

- **التوثيق الرسمي:** https://ai.google.dev/docs
- **Python SDK:** https://github.com/google/generative-ai-python
- **أمثلة:** https://ai.google.dev/examples
- **Pricing:** https://ai.google.dev/pricing

---

## 🔐 أمان API Key

### ⚠️ لا تفعل:
- ❌ لا تضع المفتاح في الكود مباشرة
- ❌ لا ترفع .env إلى Git
- ❌ لا تشارك المفتاح علناً

### ✅ افعل:
- ✅ استخدم .env للمفاتيح
- ✅ أضف .env إلى .gitignore
- ✅ استخدم مفاتيح مختلفة للتطوير والإنتاج

---

## 🎉 جاهز!

الآن يمكنك:
1. ✅ استخدام Gemini AI في المحادثات
2. ✅ تحليل نوايا المستخدمين بذكاء
3. ✅ استخراج البيانات تلقائياً
4. ✅ توليد ردود احترافية

**اختبر الآن:**
```bash
.\test_gemini_chat.ps1
```

أو افتح: http://localhost:8000/chat/
