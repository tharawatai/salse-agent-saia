# 📊 ملخص هيكلية قاعدة البيانات - SAIA

## 📈 الإحصائيات العامة

- **إجمالي الجداول**: 22 جدول
- **قاعدة البيانات**: PostgreSQL
- **Framework**: Django ORM
- **نوع البيانات المرنة**: JSONB

---

## 📋 الجداول حسب الفئة

### 1️⃣ المستخدمون والمركبات (2 جدول)
```
✓ users             - بيانات العملاء والمستخدمين
✓ vehicles          - المركبات المملوكة
```

### 2️⃣ شركات وخدمات التأمين (3 جداول)
```
✓ insurance_companies  - شركات التأمين المتعاونة
✓ insurance_services   - أنواع خدمات التأمين
✓ insurance_offers     - العروض التأمينية المتاحة
```

### 3️⃣ الطلبات والمدفوعات (4 جداول)
```
✓ insurance_orders  - طلبات التأمين
✓ invoices          - الفواتير
✓ payments          - المدفوعات
✓ policies          - وثائق التأمين الصادرة
```

### 4️⃣ نظام المحادثات (9 جداول)
```
✓ conversation_sessions          - جلسات المحادثات الرئيسية
✓ session_vehicle_data           - بيانات السيارة المجمعة
✓ session_profile_data           - بيانات العميل المجمعة
✓ session_offers_data            - العروض المعروضة والمختارة
✓ conversation_messages          - سجل الرسائل
✓ stage_transitions              - انتقالات المراحل
✓ session_results                - نتائج الجلسة النهائية
✓ session_modification_events    - أحداث التعديل والرجوع
✓ session_analytics              - التحليلات والإحصائيات
```

### 5️⃣ التكاملات الخارجية (4 جداول)
```
✓ whatsapp_sessions          - جلسات WhatsApp
✓ payment_gateway_configs    - إعدادات بوابات الدفع
✓ ai_threads                 - محادثات AI
✓ ai_messages                - رسائل AI
```

---

## 🔑 الحقول الرئيسية

### UUID Fields
- `conversation_sessions.session_id`
- `conversation_messages.message_id`

### Auto-Generated Codes
- `users.user_code` → USR12345678
- `insurance_orders.order_code` → ORD1234567890
- `invoices.invoice_no` → INV1234567890
- `policies.policy_no` → POL1234567890

### JSON/JSONB Fields
```json
insurance_offers: {
  "deductible_options": [...],
  "included_features_json": [...],
  "optional_addons_json": [...]
}

conversation_sessions: {
  "metadata": {...}
}

conversation_messages: {
  "extracted_data": {...},
  "ai_analysis": {...},
  "metadata": {...}
}

session_analytics: {
  "stages_visited": [...],
  "time_per_stage": {...}
}
```

---

## 🔗 العلاقات الأساسية

```
User ─┬─> Vehicles (1:N)
      ├─> Insurance Orders (1:N)
      └─> Conversation Sessions (1:N)

Insurance Offer ─> Insurance Order (N:1)
Vehicle ────────> Insurance Order (N:1)

Insurance Order ─┬─> Invoice (1:1)
                 ├─> Policy (1:1)
                 └─> Session Results (1:N)

Invoice ────────> Payments (1:N)

Conversation Session ─┬─> Vehicle Data (1:1)
                      ├─> Profile Data (1:1)
                      ├─> Offers Data (1:1)
                      ├─> Messages (1:N)
                      ├─> Transitions (1:N)
                      ├─> Result (1:1)
                      ├─> Analytics (1:1)
                      └─> Modification Events (1:N)
```

---

## 📊 مراحل المحادثة (12 مرحلة)

1. **greeting** - الترحيب
2. **service_details** - تفاصيل الخدمة
3. **collecting_vehicle** - جمع بيانات السيارة
4. **confirming_vehicle** - تأكيد بيانات السيارة
5. **showing_offers** - عرض العروض
6. **offer_details** - تفاصيل العرض
7. **collecting_profile** - جمع بيانات العميل
8. **confirming_profile** - تأكيد بيانات العميل
9. **order_summary** - ملخص الطلب
10. **confirmation** - التأكيد النهائي
11. **payment_pending** - انتظار الدفع
12. **completed** - مكتمل

---

## 💡 حالات الطلب (6 حالات)

```
draft                   → مسودة
awaiting_confirmation   → بانتظار التأكيد
pending_payment         → بانتظار الدفع
paid                    → مدفوع
policy_issued           → صدرت الوثيقة
cancelled               → ملغي
```

---

## 🎯 القنوات المدعومة

- ✅ WhatsApp
- ✅ Web Chat
- ✅ API
- ✅ Mobile App

---

## 🔍 الفهارس المهمة

### أداء عالي:
```sql
-- Users
idx_users_national_id
idx_users_phone
idx_users_city

-- Vehicles
idx_vehicles_plate_no
idx_vehicles_user_created

-- Offers
idx_offers_company_service
idx_offers_coverage_active
idx_offers_price

-- Orders
idx_orders_user_created
idx_orders_status
idx_orders_code

-- Sessions
idx_sessions_session_id
idx_sessions_user_identifier
idx_sessions_status_stage
idx_sessions_activity

-- Messages
idx_messages_session_created
idx_messages_role
idx_messages_stage
```

---

## 📁 الملفات المتاحة

1. **DATABASE_STRUCTURE.md** - وثيقة تفصيلية كاملة
2. **database_schema.sql** - SQL لإنشاء الجداول
3. **database_erd.dot** - مخطط ERD بصيغة DOT
4. **database_schema_diagram.png** - صورة بصرية للمخطط

---

## 🚀 دورة الحياة الكاملة

```
1. محادثة جديدة [conversation_sessions]
   ↓
2. إدخال بيانات السيارة [session_vehicle_data]
   ↓
3. عرض واختيار العروض [session_offers_data]
   ↓
4. إدخال البيانات الشخصية [session_profile_data]
   ↓
5. إنشاء طلب التأمين [insurance_orders]
   ↓
6. إصدار الفاتورة [invoices]
   ↓
7. الدفع [payments]
   ↓
8. إصدار الوثيقة [policies]
   ↓
9. تسجيل النتائج [session_results]
   ↓
10. حساب التحليلات [session_analytics]
```

---

**نظام SAIA للتأمين الذكي** 🚗💡  
*قاعدة بيانات احترافية متكاملة لإدارة التأمين*
