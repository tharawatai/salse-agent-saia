"""
اختبار API من example للتأكد من الاتصال بـ SAIA
"""
import requests
import json

# تسجيل الدخول أولاً
session = requests.Session()

# الحصول على CSRF token
login_page = session.get('http://127.0.0.1:8002/admin/login/', timeout=10)
csrf_token = session.cookies.get('csrftoken')

# تسجيل الدخول
login_data = {
    'username': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': csrf_token,
    'next': '/admin/'
}
login_response = session.post(
    'http://127.0.0.1:8002/admin/login/',
    data=login_data,
    headers={'Referer': 'http://127.0.0.1:8002/admin/login/'},
    timeout=10
)
print(f"Login status: {login_response.status_code}")

# التحقق من قائمة الـ assistants
assistants_response = session.get(
    'http://127.0.0.1:8002/ai-assistant/assistants/',
    timeout=10
)
print(f"\nAssistants API status: {assistants_response.status_code}")
if assistants_response.status_code == 200:
    try:
        assistants = assistants_response.json()
        print(f"Found {len(assistants)} assistants:")
        for a in assistants:
            print(f"  - {a.get('id')}: {a.get('name')}")
    except:
        print("Response is not JSON")
        print(assistants_response.text[:200])

# إنشاء thread جديد لـ SAIA
print("\n--- Creating new thread for SAIA ---")
csrf_token = session.cookies.get('csrftoken')
thread_response = session.post(
    'http://127.0.0.1:8002/ai-assistant/threads/',
    json={'name': 'Test SAIA', 'assistant_id': 'saia_insurance_assistant'},
    headers={
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    },
    timeout=10
)
print(f"Create thread status: {thread_response.status_code}")
if thread_response.status_code == 200:
    thread = thread_response.json()
    thread_id = thread.get('id')
    print(f"Thread ID: {thread_id}")
    
    # إرسال رسالة
    print("\n--- Sending message ---")
    csrf_token = session.cookies.get('csrftoken')
    msg_response = session.post(
        f'http://127.0.0.1:8002/ai-assistant/threads/{thread_id}/messages/',
        json={
            'content': 'السلام عليكم',
            'assistant_id': 'saia_insurance_assistant'
        },
        headers={
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        timeout=60
    )
    print(f"Send message status: {msg_response.status_code}")
    
    # جلب الرسائل
    print("\n--- Getting messages ---")
    messages_response = session.get(
        f'http://127.0.0.1:8002/ai-assistant/threads/{thread_id}/messages/',
        timeout=10
    )
    print(f"Get messages status: {messages_response.status_code}")
    if messages_response.status_code == 200:
        messages = messages_response.json()
        print(f"Found {len(messages)} messages:")
        for m in messages:
            content = m.get('content', '')[:150]
            msg_type = m.get('type', 'unknown')
            print(f"  [{msg_type}]: {content}...")
else:
    print(f"Error: {thread_response.text[:200]}")
