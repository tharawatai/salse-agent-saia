"""
Conversations Management APIs
Professional endpoints for managing conversations
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from datetime import datetime
import logging

from whatsapp_integration.models import WhatsAppSession

logger = logging.getLogger(__name__)


class ConversationPagination(PageNumberPagination):
    """Pagination للمحادثات"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ConversationsListAPIView(APIView):
    """
    GET /api/ai/conversations/
    
    قائمة المحادثات مع pagination وfiltration
    
    Query Parameters:
    - phone: فلترة حسب رقم الهاتف
    - status: فلترة حسب الحالة (active, completed, cancelled)
    - ordering: ترتيب (-created_at, -updated_at, created_at, updated_at)
    - page: رقم الصفحة
    - page_size: عدد العناصر (افتراضي 20)
    - search: بحث في المحادثات
    """
    
    def get(self, request):
        try:
            # الحصول على parameters
            phone = request.query_params.get('phone')
            status_filter = request.query_params.get('status')
            ordering = request.query_params.get('ordering', '-last_message_at')
            search = request.query_params.get('search', '').strip()
            
            # بناء Query
            queryset = WhatsAppSession.objects.all()
            
            # فلترة حسب الهاتف
            if phone:
                queryset = queryset.filter(phone_number=phone)
            
            # فلترة حسب الحالة
            if status_filter:
                stage_mapping = {
                    'active': ['greeting', 'service_details', 'collecting_vehicle', 'confirming_vehicle', 
                              'showing_offers', 'offer_details', 'collecting_profile', 'confirming_profile',
                              'order_summary', 'payment_pending'],
                    'completed': ['completed'],
                    'cancelled': ['cancelled']
                }
                
                if status_filter in stage_mapping:
                    queryset = queryset.filter(current_stage__in=stage_mapping[status_filter])
            
            # البحث في المحتوى
            if search:
                queryset = queryset.filter(
                    Q(phone_number__icontains=search) |
                    Q(conversation_id__icontains=search) |
                    Q(conversation_history__icontains=search)
                )
            
            # الترتيب
            queryset = queryset.order_by(ordering)
            
            # Pagination
            paginator = ConversationPagination()
            page = paginator.paginate_queryset(queryset, request)
            
            # تحويل إلى JSON
            conversations = []
            for session in page:
                # الحصول على آخر رسالة
                last_message = ""
                message_count = 0
                
                if session.conversation_history:
                    message_count = len(session.conversation_history)
                    for msg in reversed(session.conversation_history):
                        if msg.get('role') == 'assistant':
                            last_message = msg.get('message', '')[:100]
                            break
                
                # تحديد العنوان
                title = self._get_conversation_title(session)
                
                # تحديد التقدم
                progress = self._get_stage_progress(session.current_stage)
                
                # تحديد الحالة
                is_active = session.current_stage not in ['completed', 'cancelled']
                
                conversations.append({
                    'id': session.conversation_id or f"conv_{session.phone_number}",
                    'session_id': session.id,
                    'title': title,
                    'phone': session.phone_number,
                    'stage': session.current_stage or 'greeting',
                    'stage_label': self._get_stage_label(session.current_stage),
                    'progress': progress,
                    'last_message': last_message,
                    'message_count': message_count,
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'updated_at': session.last_message_at.isoformat() if session.last_message_at else None,
                    'is_active': is_active
                })
            
            return paginator.get_paginated_response(conversations)
            
        except Exception as e:
            logger.exception(f"Error in ConversationsListAPIView: {e}")
            return Response({
                'error': 'حدث خطأ في جلب المحادثات',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_conversation_title(self, session):
        """توليد عنوان للمحادثة"""
        stage = session.current_stage
        
        if stage in ['service_details', 'collecting_vehicle', 'confirming_vehicle']:
            return 'طلب تأمين جديد'
        elif stage in ['showing_offers', 'offer_details']:
            return 'عروض التأمين'
        elif stage in ['collecting_profile', 'confirming_profile']:
            return 'استكمال البيانات'
        elif stage in ['order_summary', 'payment_pending']:
            return 'في انتظار الدفع'
        elif stage == 'completed':
            return 'تأمين مكتمل'
        elif stage == 'cancelled':
            return 'طلب ملغي'
        else:
            return 'محادثة جديدة'
    
    def _get_stage_label(self, stage):
        """الحصول على تسمية المرحلة"""
        labels = {
            'greeting': 'البداية',
            'service_details': 'نوع التأمين',
            'collecting_vehicle': 'بيانات السيارة',
            'confirming_vehicle': 'تأكيد السيارة',
            'showing_offers': 'العروض',
            'offer_details': 'تفاصيل العرض',
            'collecting_profile': 'البيانات الشخصية',
            'confirming_profile': 'تأكيد البيانات',
            'order_summary': 'ملخص الطلب',
            'payment_pending': 'الدفع',
            'completed': 'مكتمل',
            'cancelled': 'ملغي'
        }
        return labels.get(stage, 'غير محدد')
    
    def _get_stage_progress(self, stage):
        """الحصول على نسبة التقدم"""
        progress = {
            'greeting': 10,
            'service_details': 20,
            'collecting_vehicle': 30,
            'confirming_vehicle': 45,
            'showing_offers': 55,
            'offer_details': 65,
            'collecting_profile': 75,
            'confirming_profile': 85,
            'order_summary': 90,
            'payment_pending': 95,
            'completed': 100,
            'cancelled': 0
        }
        return progress.get(stage, 10)


class ConversationDetailAPIView(APIView):
    """
    GET /api/ai/conversations/{conversation_id}/
    
    تفاصيل محادثة معينة مع جميع الرسائل
    """
    
    def get(self, request, conversation_id):
        try:
            # البحث عن الجلسة
            session = WhatsAppSession.objects.filter(
                Q(conversation_id=conversation_id) | 
                Q(phone_number=conversation_id.replace('conv_', ''))
            ).first()
            
            if not session:
                return Response({
                    'error': 'المحادثة غير موجودة'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # تحويل الرسائل
            messages = []
            if session.conversation_history:
                for idx, msg in enumerate(session.conversation_history):
                    messages.append({
                        'id': idx + 1,
                        'role': msg.get('role', 'user'),
                        'content': msg.get('message', ''),
                        'timestamp': msg.get('timestamp', '')
                    })
            
            # بناء الاستجابة
            detail = {
                'id': session.conversation_id or f"conv_{session.phone_number}",
                'session_id': session.id,
                'title': self._get_conversation_title(session),
                'phone': session.phone_number,
                'stage': session.current_stage or 'greeting',
                'stage_label': self._get_stage_label(session.current_stage),
                'progress': self._get_stage_progress(session.current_stage),
                'messages': messages,
                'metadata': session.context_data or {},
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'updated_at': session.last_message_at.isoformat() if session.last_message_at else None,
                'is_active': session.current_stage not in ['completed', 'cancelled']
            }
            
            return Response(detail)
            
        except Exception as e:
            logger.exception(f"Error in ConversationDetailAPIView: {e}")
            return Response({
                'error': 'حدث خطأ في جلب تفاصيل المحادثة',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_conversation_title(self, session):
        """توليد عنوان للمحادثة"""
        stage = session.current_stage
        
        if stage in ['service_details', 'collecting_vehicle', 'confirming_vehicle']:
            return 'طلب تأمين جديد'
        elif stage in ['showing_offers', 'offer_details']:
            return 'عروض التأمين'
        elif stage in ['collecting_profile', 'confirming_profile']:
            return 'استكمال البيانات'
        elif stage in ['order_summary', 'payment_pending']:
            return 'في انتظار الدفع'
        elif stage == 'completed':
            return 'تأمين مكتمل'
        elif stage == 'cancelled':
            return 'طلب ملغي'
        else:
            return 'محادثة جديدة'
    
    def _get_stage_label(self, stage):
        """الحصول على تسمية المرحلة"""
        labels = {
            'greeting': 'البداية',
            'service_details': 'نوع التأمين',
            'collecting_vehicle': 'بيانات السيارة',
            'confirming_vehicle': 'تأكيد السيارة',
            'showing_offers': 'العروض',
            'offer_details': 'تفاصيل العرض',
            'collecting_profile': 'البيانات الشخصية',
            'confirming_profile': 'تأكيد البيانات',
            'order_summary': 'ملخص الطلب',
            'payment_pending': 'الدفع',
            'completed': 'مكتمل',
            'cancelled': 'ملغي'
        }
        return labels.get(stage, 'غير محدد')
    
    def _get_stage_progress(self, stage):
        """الحصول على نسبة التقدم"""
        progress = {
            'greeting': 10,
            'service_details': 20,
            'collecting_vehicle': 30,
            'confirming_vehicle': 45,
            'showing_offers': 55,
            'offer_details': 65,
            'collecting_profile': 75,
            'confirming_profile': 85,
            'order_summary': 90,
            'payment_pending': 95,
            'completed': 100,
            'cancelled': 0
        }
        return progress.get(stage, 10)


class ConversationDeleteAPIView(APIView):
    """
    DELETE /api/ai/conversations/{conversation_id}/
    
    حذف محادثة
    """
    
    def delete(self, request, conversation_id):
        try:
            # البحث عن الجلسة
            session = WhatsAppSession.objects.filter(
                Q(conversation_id=conversation_id) | 
                Q(phone_number=conversation_id.replace('conv_', ''))
            ).first()
            
            if not session:
                return Response({
                    'error': 'المحادثة غير موجودة'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # حذف الجلسة
            session.delete()
            
            return Response({
                'success': True,
                'message': 'تم حذف المحادثة بنجاح'
            })
            
        except Exception as e:
            logger.exception(f"Error in ConversationDeleteAPIView: {e}")
            return Response({
                'error': 'حدث خطأ في حذف المحادثة',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConversationsSearchAPIView(APIView):
    """
    GET /api/ai/conversations/search/?q={query}
    
    بحث في المحادثات
    """
    
    def get(self, request):
        try:
            query = request.query_params.get('q', '').strip()
            
            if not query:
                return Response({
                    'error': 'يرجى إدخال نص البحث'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # البحث
            queryset = WhatsAppSession.objects.filter(
                Q(phone_number__icontains=query) |
                Q(conversation_id__icontains=query) |
                Q(conversation_history__icontains=query)
            ).order_by('-last_message_at')
            
            # Pagination
            paginator = ConversationPagination()
            page = paginator.paginate_queryset(queryset, request)
            
            # تحويل النتائج
            results = []
            for session in page:
                last_message = ""
                message_count = 0
                
                if session.conversation_history:
                    message_count = len(session.conversation_history)
                    for msg in reversed(session.conversation_history):
                        if msg.get('role') == 'assistant':
                            last_message = msg.get('message', '')[:100]
                            break
                
                results.append({
                    'id': session.conversation_id or f"conv_{session.phone_number}",
                    'session_id': session.id,
                    'title': self._get_conversation_title(session),
                    'phone': session.phone_number,
                    'stage': session.current_stage or 'greeting',
                    'stage_label': self._get_stage_label(session.current_stage),
                    'progress': self._get_stage_progress(session.current_stage),
                    'last_message': last_message,
                    'message_count': message_count,
                    'created_at': session.created_at.isoformat() if session.created_at else None,
                    'updated_at': session.last_message_at.isoformat() if session.last_message_at else None,
                    'is_active': session.current_stage not in ['completed', 'cancelled']
                })
            
            return paginator.get_paginated_response(results)
            
        except Exception as e:
            logger.exception(f"Error in ConversationsSearchAPIView: {e}")
            return Response({
                'error': 'حدث خطأ في البحث',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_conversation_title(self, session):
        """توليد عنوان للمحادثة"""
        stage = session.current_stage
        
        if stage in ['service_details', 'collecting_vehicle', 'confirming_vehicle']:
            return 'طلب تأمين جديد'
        elif stage in ['showing_offers', 'offer_details']:
            return 'عروض التأمين'
        elif stage in ['collecting_profile', 'confirming_profile']:
            return 'استكمال البيانات'
        elif stage in ['order_summary', 'payment_pending']:
            return 'في انتظار الدفع'
        elif stage == 'completed':
            return 'تأمين مكتمل'
        elif stage == 'cancelled':
            return 'طلب ملغي'
        else:
            return 'محادثة جديدة'
    
    def _get_stage_label(self, stage):
        """الحصول على تسمية المرحلة"""
        labels = {
            'greeting': 'البداية',
            'service_details': 'نوع التأمين',
            'collecting_vehicle': 'بيانات السيارة',
            'confirming_vehicle': 'تأكيد السيارة',
            'showing_offers': 'العروض',
            'offer_details': 'تفاصيل العرض',
            'collecting_profile': 'البيانات الشخصية',
            'confirming_profile': 'تأكيد البيانات',
            'order_summary': 'ملخص الطلب',
            'payment_pending': 'الدفع',
            'completed': 'مكتمل',
            'cancelled': 'ملغي'
        }
        return labels.get(stage, 'غير محدد')
    
    def _get_stage_progress(self, stage):
        """الحصول على نسبة التقدم"""
        progress = {
            'greeting': 10,
            'service_details': 20,
            'collecting_vehicle': 30,
            'confirming_vehicle': 45,
            'showing_offers': 55,
            'offer_details': 65,
            'collecting_profile': 75,
            'confirming_profile': 85,
            'order_summary': 90,
            'payment_pending': 95,
            'completed': 100,
            'cancelled': 0
        }
        return progress.get(stage, 10)


class ConversationsStatsAPIView(APIView):
    """
    GET /api/ai/conversations/stats/
    
    إحصائيات المحادثات
    """
    
    def get(self, request):
        try:
            phone = request.query_params.get('phone')
            
            queryset = WhatsAppSession.objects.all()
            
            if phone:
                queryset = queryset.filter(phone_number=phone)
            
            # حساب الإحصائيات
            total = queryset.count()
            active = queryset.filter(
                current_stage__in=['greeting', 'service_details', 'collecting_vehicle', 
                                  'confirming_vehicle', 'showing_offers', 'offer_details',
                                  'collecting_profile', 'confirming_profile', 
                                  'order_summary', 'payment_pending']
            ).count()
            completed = queryset.filter(current_stage='completed').count()
            cancelled = queryset.filter(current_stage='cancelled').count()
            
            return Response({
                'total': total,
                'active': active,
                'completed': completed,
                'cancelled': cancelled,
                'stats_by_stage': self._get_stage_stats(queryset)
            })
            
        except Exception as e:
            logger.exception(f"Error in ConversationsStatsAPIView: {e}")
            return Response({
                'error': 'حدث خطأ في جلب الإحصائيات',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_stage_stats(self, queryset):
        """إحصائيات حسب المرحلة"""
        stages = queryset.values('current_stage').annotate(
            count=Count('id')
        ).order_by('-count')
        
        result = {}
        for stage in stages:
            if stage['current_stage']:
                result[stage['current_stage']] = stage['count']
        
        return result
