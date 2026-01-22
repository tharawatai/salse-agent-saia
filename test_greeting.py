"""
اختبار رسالة الترحيب والهوية
"""
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/ai/chat/"

def test_greeting():
    """اختبار رسالة الترحيب"""
    print("\n" + "="*60)
    print("🎯 اختبار 1: رسالة الترحيب")
    print("="*60)
    
    conv_id = str(uuid.uuid4())
    
    response = requests.post(
        API_URL,
        json={"message": "مرحبا", "conversation_id": conv_id},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"📥 الرد:\n{data.get('response', '')}")
        print("\n✅ تم اختبار الترحيب")
    else:
        print(f"❌ فشل: {response.status_code}")

def test_identity():
    """اختبار سؤال الهوية"""
    print("\n" + "="*60)
    print("🎯 اختبار 2: سؤال 'من أنت؟'")
    print("="*60)
    
    conv_id = str(uuid.uuid4())
    
    response = requests.post(
        API_URL,
        json={"message": "من أنت؟", "conversation_id": conv_id},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        reply = data.get('response', '')
        print(f"📥 الرد:\n{reply}")
        
        # التحقق من ذكر المعلومات
        checks = [
            ("سايا" in reply or "SAIA" in reply, "اسم سايا"),
            ("كونكورد" in reply, "شركة كونكورد"),
            ("Bineyes" in reply or "بنايص" in reply, "شركة Bineyes"),
        ]
        
        print("\n🔍 التحقق:")
        for check, name in checks:
            status = "✅" if check else "❌"
            print(f"   {status} {name}")
    else:
        print(f"❌ فشل: {response.status_code}")

if __name__ == "__main__":
    test_greeting()
    test_identity()
    print("\n" + "="*60)
    print("✅ انتهى الاختبار")
    print("="*60)
