"""
اختبار سيناريو كامل من example API
"""
import requests
import time

# تسجيل الدخول
session = requests.Session()
login_page = session.get('http://127.0.0.1:8002/admin/login/', timeout=10)
csrf_token = session.cookies.get('csrftoken')

login_data = {
    'username': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': csrf_token,
    'next': '/admin/'
}
session.post(
    'http://127.0.0.1:8002/admin/login/',
    data=login_data,
    headers={'Referer': 'http://127.0.0.1:8002/admin/login/'},
    timeout=10
)

# إنشاء thread
csrf_token = session.cookies.get('csrftoken')
thread_response = session.post(
    'http://127.0.0.1:8002/ai-assistant/threads/',
    json={'name': 'Full Test', 'assistant_id': 'saia_insurance_assistant'},
    headers={'Content-Type': 'application/json', 'X-CSRFToken': csrf_token},
    timeout=10
)
thread_id = thread_response.json().get('id')
print(f"Thread ID: {thread_id}")

def send_and_get(message):
    csrf_token = session.cookies.get('csrftoken')
    session.post(
        f'http://127.0.0.1:8002/ai-assistant/threads/{thread_id}/messages/',
        json={'content': message, 'assistant_id': 'saia_insurance_assistant'},
        headers={'Content-Type': 'application/json', 'X-CSRFToken': csrf_token},
        timeout=90
    )
    messages = session.get(
        f'http://127.0.0.1:8002/ai-assistant/threads/{thread_id}/messages/',
        timeout=10
    ).json()
    # آخر رسالة AI
    for m in reversed(messages):
        if m.get('type') == 'ai':
            return m.get('content', '')[:300]
    return "No AI response"

print("\n" + "="*60)
print("Full Scenario Test via Example API")
print("="*60)

# 1. الترحيب
print("\n[1] Greeting...")
response = send_and_get("السلام عليكم")
print(f"Response: {response}...")
time.sleep(1)

# 2. اختيار الخدمة
print("\n[2] Service Selection...")
response = send_and_get("تأمين شامل")
print(f"Response: {response}...")
time.sleep(1)

# 3. بيانات السيارة
print("\n[3] Vehicle Data...")
response = send_and_get("تويوتا كامري 2024 قيمتها 150000 لوحة أ ب ج 5678")
print(f"Response: {response}...")
time.sleep(1)

# 4. تأكيد السيارة
print("\n[4] Confirm Vehicle...")
response = send_and_get("نعم صحيحة")
print(f"Response: {response}...")
time.sleep(1)

# 5. اختيار العرض
print("\n[5] Select Offer...")
response = send_and_get("العرض 1")
print(f"Response: {response}...")
time.sleep(1)

# 6. تأكيد العرض
print("\n[6] Confirm Offer...")
response = send_and_get("موافق")
print(f"Response: {response}...")
time.sleep(1)

# 7. البيانات الشخصية
print("\n[7] Profile Data...")
response = send_and_get("رقم هويتي 1122334455 وتاريخ ميلادي 1985-03-20")
print(f"Response: {response}...")
time.sleep(1)

# 8. تأكيد البيانات
print("\n[8] Confirm Profile...")
response = send_and_get("نعم صحيحة")
print(f"Response: {response}...")
time.sleep(1)

# 9. تأكيد الطلب
print("\n[9] Confirm Order...")
response = send_and_get("تأكيد الطلب")
print(f"Response: {response}...")
time.sleep(1)

# 10. الدفع
print("\n[10] Payment...")
response = send_and_get("تم الدفع")
print(f"Response: {response}...")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)
