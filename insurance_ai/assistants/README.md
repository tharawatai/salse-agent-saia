# SAIA Assistants Module

هيكلية متوافقة مع `django_ai_assistant` لكن تستخدم **Gemini** بدلاً من OpenAI/LangChain.

## الهيكلية

```
assistants/
├── __init__.py          # تصدير الـ classes
├── base.py              # AIAssistant base class
├── insurance_assistant.py  # المساعد الرئيسي
├── tools/
│   ├── __init__.py
│   └── insurance_tools.py  # أدوات مستقلة
└── README.md
```

## الاستخدام

### 1. إنشاء مساعد جديد

```python
from insurance_ai.assistants import AIAssistant, method_tool

class MyAssistant(AIAssistant):
    id = "my-assistant"
    name = "مساعدي"
    instructions = "أنت مساعد ذكي..."
    model = "gemini-2.0-flash"
    
    @method_tool(description="وصف الأداة")
    async def my_tool(self, param: str) -> dict:
        return {"result": param}
    
    async def run(self, message: str, thread_id=None, **kwargs):
        # منطق المعالجة
        pass
```

### 2. استخدام المساعد

```python
from insurance_ai.assistants import InsuranceAssistant

assistant = InsuranceAssistant(user=request.user)
result = await assistant.run(
    message="أريد تأمين سيارتي",
    thread_id="conv_123",
    phone="0501234567"
)
```

### 3. API Endpoints

```
GET  /api/ai/v2/assistants/           # قائمة المساعدين
GET  /api/ai/v2/assistants/{id}/      # معلومات مساعد

GET  /api/ai/v2/threads/              # قائمة المحادثات
POST /api/ai/v2/threads/              # إنشاء محادثة
GET  /api/ai/v2/threads/{id}/         # معلومات محادثة

GET  /api/ai/v2/threads/{id}/messages/    # رسائل المحادثة
POST /api/ai/v2/threads/{id}/messages/    # إرسال رسالة

POST /api/ai/v2/chat/                 # محادثة سريعة (بدون thread)
```

## التوافق مع django_ai_assistant

| django_ai_assistant | SAIA |
|---------------------|------|
| OpenAI/LangChain | Gemini |
| `@method_tool` | `@method_tool` ✓ |
| `AIAssistant` base | `AIAssistant` base ✓ |
| Thread/Message models | Thread/Message models ✓ |
| Ninja API | Ninja API ✓ |
| use_cases helpers | use_cases helpers ✓ |

## الفرق الرئيسي

1. **المحرك**: يستخدم `ProfessionalInsuranceEngineV2` داخلياً
2. **LLM**: Gemini بدلاً من OpenAI
3. **Tools**: مبسطة (بدون LangChain tools)
4. **RAG**: غير مدعوم حالياً (يمكن إضافته)
