# 🚀 سكريبت البدء السريع - SAIA Project
# يقوم بتشغيل جميع الخطوات اللازمة لبدء المشروع

Write-Host "🚀 بدء تشغيل مشروع SAIA..." -ForegroundColor Green
Write-Host ""

# 1. التحقق من البيئة الافتراضية
Write-Host "1️⃣ التحقق من البيئة الافتراضية..." -ForegroundColor Cyan
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "   ✅ البيئة الافتراضية موجودة" -ForegroundColor Green
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host "   ❌ البيئة الافتراضية غير موجودة!" -ForegroundColor Red
    Write-Host "   قم بإنشائها أولاً: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# 2. التحقق من قاعدة البيانات
Write-Host ""
Write-Host "2️⃣ التحقق من قاعدة البيانات..." -ForegroundColor Cyan
if (Test-Path "db.sqlite3") {
    Write-Host "   ✅ قاعدة البيانات موجودة" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ قاعدة البيانات غير موجودة - سيتم إنشاؤها" -ForegroundColor Yellow
    .\venv\Scripts\python.exe manage.py migrate
}

# 3. التحقق من حساب المدير
Write-Host ""
Write-Host "3️⃣ التحقق من حساب المدير..." -ForegroundColor Cyan
$adminExists = .\venv\Scripts\python.exe -c "import django; django.setup(); from insurance_core.models import User; print(User.objects.filter(username='admin').exists())"
if ($adminExists -eq "True") {
    Write-Host "   ✅ حساب المدير موجود" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ حساب المدير غير موجود - سيتم إنشاؤه" -ForegroundColor Yellow
    .\venv\Scripts\python.exe scripts\create_superuser.py
}

# 4. التحقق من البيانات التجريبية
Write-Host ""
Write-Host "4️⃣ التحقق من البيانات التجريبية..." -ForegroundColor Cyan
$companiesCount = .\venv\Scripts\python.exe -c "import django; django.setup(); from insurance_core.models import InsuranceCompany; print(InsuranceCompany.objects.count())"
if ([int]$companiesCount -ge 5) {
    Write-Host "   ✅ البيانات التجريبية موجودة ($companiesCount شركات)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ البيانات التجريبية قليلة - سيتم إضافة المزيد" -ForegroundColor Yellow
    .\venv\Scripts\python.exe scripts\add_sample_data.py
}

# 5. عرض معلومات النظام
Write-Host ""
Write-Host "📊 معلومات النظام:" -ForegroundColor Cyan
Write-Host "   🌐 عنوان الخادم: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   🔐 لوحة التحكم: http://127.0.0.1:8000/admin/" -ForegroundColor White
Write-Host "   👤 اسم المستخدم: admin" -ForegroundColor White
Write-Host "   🔑 كلمة المرور: admin123" -ForegroundColor White

# 6. تشغيل الخادم
Write-Host ""
Write-Host "🚀 تشغيل الخادم..." -ForegroundColor Green
Write-Host "   اضغط Ctrl+C لإيقاف الخادم" -ForegroundColor Yellow
Write-Host ""

.\venv\Scripts\python.exe manage.py runserver
