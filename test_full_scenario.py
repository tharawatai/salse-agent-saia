"""
اختبار سيناريو كامل لـ SAIA
"""
import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000'
CHAT_URL = f'{BASE_URL}/api/ai/chat/'

# رقم هاتف فريد للاختبار
phone = '966551234999'
conv_id = None

def send_message(msg):
    global conv_id
    payload = {'message': msg, 'phone': phone}
    if conv_id:
        payload['conversation_id'] = conv_id
    
    try:
        r = requests.post(CHAT_URL, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            if not conv_id:
                conv_id = data.get('conversation_id')
            return data
        else:
            print(f'Error: {r.status_code}')
            print(r.text)
            return None
    except Exception as e:
        print(f'Exception: {e}')
        return None

def print_result(step, result):
    if result:
        stage = result.get('stage', 'N/A')
        response = result.get('response', '')[:300]
        print(f"\n{'='*60}")
        print(f"[{step}] Stage: {stage}")
        print(f"Response: {response}...")
        if result.get('has_invoice'):
            print(f"Invoice URL: {result.get('invoice_url')}")
        if result.get('has_policy'):
            print(f"Policy URL: {result.get('policy_url')}")
    else:
        print(f"\n[{step}] FAILED!")

print('='*60)
print('SAIA Full Scenario Test')
print('='*60)

# 1. الترحيب
result = send_message('السلام عليكم')
print_result('1-Greeting', result)
time.sleep(1)

# 2. اختيار الخدمة
result = send_message('اريد تأمين شامل')
print_result('2-Service', result)
time.sleep(1)

# 3. بيانات السيارة
vehicle_msg = """ماركة السيارة: تويوتا
موديل السيارة: كامري
سنة الصنع: 2023
قيمة السيارة: 120000
رقم اللوحة: أ ب ج 1234"""
result = send_message(vehicle_msg)
print_result('3-Vehicle', result)
time.sleep(1)

# 4. تأكيد بيانات السيارة
result = send_message('نعم صحيحة')
print_result('4-ConfirmVehicle', result)
time.sleep(1)

# 5. اختيار العرض
result = send_message('اختار العرض رقم 2')
print_result('5-SelectOffer', result)
time.sleep(1)

# 6. تأكيد العرض
result = send_message('نعم موافق')
print_result('6-ConfirmOffer', result)
time.sleep(1)

# 7. البيانات الشخصية
profile_msg = """رقم الهوية: 1234567890
تاريخ الميلاد: 1990-05-15"""
result = send_message(profile_msg)
print_result('7-Profile', result)
time.sleep(1)

# 8. تأكيد البيانات الشخصية
result = send_message('نعم صحيحة')
print_result('8-ConfirmProfile', result)
time.sleep(1)

# 9. تأكيد الطلب
result = send_message('نعم أكد الطلب')
print_result('9-ConfirmOrder', result)
time.sleep(1)

# 10. تأكيد الدفع
result = send_message('تم الدفع')
print_result('10-Payment', result)

print('\n' + '='*60)
print('Test Complete!')
print('='*60)
