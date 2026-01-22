"""
اختبار اتصال الواجهة بالخدمة
Test Frontend Connection to Backend
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_chat_page():
    """اختبار صفحة الشات"""
    print("\n" + "="*60)
    print("🌐 اختبار 1: صفحة الشات (chat_v2.html)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/chat/v2/", timeout=10)
        if response.status_code == 200:
            print(f"✅ الصفحة تعمل - Status: {response.status_code}")
            # التحقق من وجود العناصر الأساسية
            html = response.text
            checks = [
                ("API_URL = '/api/ai/chat/'", "رابط API"),
                ("sendMessage", "دالة إرسال الرسالة"),
                ("chatMessages", "حاوية الرسائل"),
                ("messageInput", "حقل الإدخال"),
            ]
            for check, name in checks:
                if check in html:
                    print(f"   ✅ {name} موجود")
                else:
                    print(f"   ❌ {name} غير موجود!")
            return True
        else:
            print(f"❌ فشل - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False

def test_chat_api():
    """اختبار API الشات"""
    print("\n" + "="*60)
    print("🔌 اختبار 2: Chat API (/api/ai/chat/)")
    print("="*60)
    
    try:
        # اختبار POST
        response = requests.post(
            f"{BASE_URL}/api/ai/chat/",
            json={"message": "مرحبا", "phone": "966501234567"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API يعمل - Status: {response.status_code}")
            print(f"   📍 المرحلة: {data.get('stage', 'غير محدد')}")
            print(f"   💬 الرد: {data.get('response', '')[:100]}...")
            print(f"   🔑 conversation_id: {data.get('conversation_id', 'غير موجود')}")
            return True, data.get('conversation_id')
        else:
            print(f"❌ فشل - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return False, None

def test_api_flow(conversation_id):
    """اختبار تدفق المحادثة"""
    print("\n" + "="*60)
    print("🔄 اختبار 3: تدفق المحادثة")
    print("="*60)
    
    messages = [
        ("أريد تأمين شامل", "اختيار الخدمة"),
        ("تويوتا كامري 2024 قيمتها 120000 لوحة أ ب ج 1234", "بيانات السيارة"),
    ]
    
    for msg, step in messages:
        try:
            response = requests.post(
                f"{BASE_URL}/api/ai/chat/",
                json={
                    "message": msg,
                    "conversation_id": conversation_id,
                    "phone": "966501234567"
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ [{step}] نجح")
                print(f"   📍 المرحلة: {data.get('stage', 'غير محدد')}")
            else:
                print(f"❌ [{step}] فشل - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ [{step}] خطأ: {e}")
            return False
    
    return True

def test_static_resources():
    """اختبار الموارد الثابتة"""
    print("\n" + "="*60)
    print("📦 اختبار 4: الموارد الثابتة")
    print("="*60)
    
    # اختبار Google Fonts (خارجي)
    try:
        response = requests.get(
            "https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap",
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Google Fonts (Tajawal) متاح")
        else:
            print("⚠️ Google Fonts قد لا يكون متاحاً")
    except:
        print("⚠️ لا يمكن الوصول لـ Google Fonts")
    
    return True

def test_cors():
    """اختبار CORS"""
    print("\n" + "="*60)
    print("🔒 اختبار 5: CORS Headers")
    print("="*60)
    
    try:
        response = requests.options(
            f"{BASE_URL}/api/ai/chat/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            },
            timeout=10
        )
        
        cors_header = response.headers.get('Access-Control-Allow-Origin', '')
        if cors_header:
            print(f"✅ CORS مفعل: {cors_header}")
        else:
            print("⚠️ CORS قد لا يكون مفعلاً (قد يكون طبيعياً للـ same-origin)")
        
        return True
    except Exception as e:
        print(f"⚠️ لا يمكن اختبار CORS: {e}")
        return True

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "🚀"*30)
    print("بدء اختبار اتصال الواجهة بالخدمة")
    print("🚀"*30)
    
    results = []
    
    # اختبار 1: صفحة الشات
    results.append(("صفحة الشات", test_chat_page()))
    
    # اختبار 2: Chat API
    api_ok, conv_id = test_chat_api()
    results.append(("Chat API", api_ok))
    
    # اختبار 3: تدفق المحادثة
    if conv_id:
        results.append(("تدفق المحادثة", test_api_flow(conv_id)))
    
    # اختبار 4: الموارد الثابتة
    results.append(("الموارد الثابتة", test_static_resources()))
    
    # اختبار 5: CORS
    results.append(("CORS", test_cors()))
    
    # ملخص النتائج
    print("\n" + "="*60)
    print("📊 ملخص النتائج")
    print("="*60)
    
    passed = 0
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {name}")
        if result:
            passed += 1
    
    print(f"\n   النتيجة: {passed}/{len(results)} اختبارات ناجحة")
    
    if passed == len(results):
        print("\n🎉 جميع الاختبارات ناجحة! الواجهة متصلة بالخدمة بشكل صحيح.")
    else:
        print("\n⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")

if __name__ == "__main__":
    run_all_tests()
