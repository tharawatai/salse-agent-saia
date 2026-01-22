"""
سيناريو اختبار الشات - Test Chat Scenario
"""
import requests
import json
import time
import uuid

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/ai/chat/"

# معرف محادثة فريد
CONVERSATION_ID = str(uuid.uuid4())

def send_message(message: str, step_name: str = ""):
    """إرسال رسالة والحصول على الرد"""
    print(f"\n{'='*60}")
    print(f"📤 [{step_name}] إرسال: {message}")
    print('='*60)
    
    try:
        response = requests.post(
            API_URL,
            json={
                "message": message,
                "conversation_id": CONVERSATION_ID
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📥 الرد:")
            print("-"*40)
            print(data.get('response', 'لا يوجد رد'))
            print("-"*40)
            print(f"📍 المرحلة: {data.get('stage', 'غير محدد')}")
            
            # عرض بيانات السيارة إذا وجدت
            if data.get('vehicle_data'):
                print(f"🚗 بيانات السيارة: {json.dumps(data['vehicle_data'], ensure_ascii=False, indent=2)}")
            
            return data
        else:
            print(f"❌ خطأ: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ استثناء: {e}")
        return None

def run_scenario():
    """تشغيل سيناريو الاختبار الكامل"""
    print("\n" + "🚀"*30)
    print("بدء سيناريو اختبار الشات")
    print("🚀"*30)
    
    # الخطوة 1: التحية
    result = send_message("السلام عليكم", "التحية")
    time.sleep(2)
    
    # الخطوة 2: طلب التأمين الشامل
    result = send_message("أريد تأمين شامل", "اختيار الخدمة")
    time.sleep(2)
    
    # الخطوة 3: إرسال بيانات السيارة كاملة
    result = send_message(
        "تويوتا كامري 2024 قيمتها 120000 لوحة أ ب ج 1234",
        "بيانات السيارة"
    )
    time.sleep(2)
    
    # التحقق من استخراج اللوحة
    if result:
        vehicle = result.get('vehicle_data', {})
        plate = vehicle.get('plate_no', '')
        print(f"\n🔍 التحقق من اللوحة:")
        print(f"   اللوحة المستخرجة: '{plate}'")
        if 'أ ب ج' in plate or '1234' in plate:
            print("   ✅ تم استخراج اللوحة بشكل صحيح!")
        else:
            print("   ❌ مشكلة في استخراج اللوحة")
    
    # الخطوة 4: تأكيد البيانات
    result = send_message("نعم صحيحة", "تأكيد السيارة")
    time.sleep(2)
    
    # الخطوة 5: اختيار عرض
    if result and 'العروض' in result.get('response', ''):
        result = send_message("العرض 1", "اختيار العرض")
        time.sleep(2)
    
    # الخطوة 6: تأكيد العرض
    if result:
        result = send_message("نعم أوافق", "تأكيد العرض")
        time.sleep(2)
    
    # الخطوة 7: البيانات الشخصية
    if result and 'الهوية' in result.get('response', ''):
        result = send_message("1234567890 1990-05-15", "البيانات الشخصية")
        time.sleep(2)
    
    print("\n" + "✅"*30)
    print("انتهى سيناريو الاختبار")
    print("✅"*30)

if __name__ == "__main__":
    run_scenario()
