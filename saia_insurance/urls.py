"""URL Configuration لمشروع SAIA"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('ai-assistant/', include('django_ai_assistant.urls')),  # تعطيل مؤقتاً
    path('api/whatsapp/', include('whatsapp_integration.urls')),
    path('api/insurance/', include('insurance_core.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/ai/', include('insurance_ai.urls')),  # Chat API
    path('chat/', TemplateView.as_view(template_name='chat.html'), name='chat'),  # Chat UI (Legacy)
    path('chat/v2/', TemplateView.as_view(template_name='chat_v2.html'), name='chat_v2'),  # Chat UI v2 (New API)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "SAIA - لوحة التحكم"
admin.site.site_title = "SAIA Admin"
admin.site.index_title = "مرحباً بك في نظام SAIA"
