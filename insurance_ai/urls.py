"""
URLs للـ AI Chat
يدعم كلاً من:
1. API القديم (REST) - للتوافق
2. API الجديد (Ninja) - متوافق مع django_ai_assistant
"""
from django.urls import path

# Legacy REST API
from .chat_views import (
    ChatAPIView, 
    ChatHistoryAPIView, 
    ChatResetAPIView,
    CustomerDataAPIView,
    InvoicePDFView,
    PolicyPDFView
)

# Conversations Management API
from .conversations_api import (
    ConversationsListAPIView,
    ConversationDetailAPIView,
    ConversationDeleteAPIView,
    ConversationsSearchAPIView,
    ConversationsStatsAPIView
)

# New Ninja API (django_ai_assistant compatible)
from .api.views import api as ninja_api

app_name = 'insurance_ai'

urlpatterns = [
    # ==================== Legacy REST API ====================
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('chat/<int:session_id>/history/', ChatHistoryAPIView.as_view(), name='chat-history'),
    path('chat/<int:session_id>/reset/', ChatResetAPIView.as_view(), name='chat-reset'),
    path('customer-data/', CustomerDataAPIView.as_view(), name='customer-data'),
    
    # PDF Downloads
    path('invoices/<int:invoice_id>/pdf/', InvoicePDFView.as_view(), name='invoice-pdf'),
    path('policies/<int:policy_id>/pdf/', PolicyPDFView.as_view(), name='policy-pdf'),
    
    # ==================== Conversations Management API ====================
    path('conversations/', ConversationsListAPIView.as_view(), name='conversations-list'),
    path('conversations/search/', ConversationsSearchAPIView.as_view(), name='conversations-search'),
    path('conversations/stats/', ConversationsStatsAPIView.as_view(), name='conversations-stats'),
    path('conversations/<str:conversation_id>/', ConversationDetailAPIView.as_view(), name='conversation-detail'),
    path('conversations/<str:conversation_id>/delete/', ConversationDeleteAPIView.as_view(), name='conversation-delete'),
    
    # ==================== New Ninja API ====================
    # متوافق مع django_ai_assistant
    # /api/ai/v2/assistants/
    # /api/ai/v2/threads/
    # /api/ai/v2/threads/{id}/messages/
    path('v2/', ninja_api.urls),
]
