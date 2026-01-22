"""
Chat API للتواصل مع AI Sales Agent
مستوحى من النظام الاحترافي في feat/whatsapp-webhock
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from datetime import datetime
import logging
import importlib
import sys

from insurance_core.models import User
from whatsapp_integration.models import WhatsAppSession

# 🆕 استخدام Factory Pattern من الهيكلية الجديدة
from .factory import get_professional_engine, reset_professional_engine

logger = logging.getLogger(__name__)


class ChatAPIView(APIView):
    """
    API للمحادثة مع AI Sales Agent
    """
    
    def post(self, request):
        """
        إرسال رسالة والحصول على رد
        
        Body:
        {
            "message": "مرحباً، أريد تأمين سيارتي",
            "conversation_id": "conv_123",  # اختياري
            "user_id": 1,  # اختياري
            "phone": "0501234567"  # اختياري
        }
        """
        message = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id')
        user_id = request.data.get('user_id')
        phone = request.data.get('phone')
        
        if not message:
            return Response({
                'error': 'الرسالة مطلوبة'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 🆕 استخدام phone كمعرف أساسي للجلسة
        # إذا لم يتم توفير conversation_id، استخدم phone أو أنشئ واحد جديد
        if not conversation_id:
            if phone:
                # استخدام phone كـ conversation_id لضمان استمرارية الجلسة
                conversation_id = f"conv_{phone}"
            else:
                import uuid
                conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        # الحصول على المستخدم
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass
        
        # الحصول على أو إنشاء جلسة
        session = None
        if phone:
            session, created = WhatsAppSession.objects.get_or_create(
                phone_number=phone,
                defaults={'user': user}
            )
            if user and not session.user:
                session.user = user
                session.save()
        
        try:
            # 🆕 تم إزالة إعادة التعيين في DEBUG mode لأنها تمسح السياق
            # إذا كنت تريد إعادة تحميل الكود، أعد تشغيل السيرفر يدوياً
            
            # الحصول على المحرك
            engine = get_professional_engine()
            
            # معالجة الرسالة باستخدام المحرك الاحترافي V2
            import asyncio
            result = asyncio.run(
                engine.process_message(
                    conversation_id=conversation_id,
                    message=message,
                    user=user,
                    phone=phone
                )
            )
            
            # حفظ المحادثة في الجلسة
            if session:
                conversation = session.conversation_history or []
                conversation.append({
                    'role': 'user',
                    'message': message,
                    'timestamp': str(datetime.now())
                })
                conversation.append({
                    'role': 'assistant',
                    'message': result.response_message,
                    'timestamp': str(datetime.now())
                })
                session.conversation_history = conversation
                session.save()
            
            return Response({
                'success': result.success,
                'message': message,
                'response': result.response_message,
                'conversation_id': conversation_id,
                'user_id': user.id if user else None,
                'session_id': session.id if session else None,
                'stage': result.next_stage.value if result.next_stage else None,
                'data': result.data_collected if hasattr(result, 'data_collected') else None,
                'conversation_count': len(conversation) if session else 0,
                'error': result.error if hasattr(result, 'error') else None,
                'has_invoice': getattr(result, 'has_invoice', False),
                'invoice_url': getattr(result, 'invoice_url', None),
                'invoice_pdf_path': getattr(result, 'invoice_pdf_path', None),
                'has_policy': getattr(result, 'has_policy', False),
                'policy_url': getattr(result, 'policy_url', None),
                'policy_pdf_path': getattr(result, 'policy_pdf_path', None),
            })
            
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'message': 'حدث خطأ أثناء معالجة الرسالة'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatHistoryAPIView(APIView):
    """
    API للحصول على تاريخ المحادثة
    """
    
    def get(self, request, session_id):
        """
        الحصول على تاريخ المحادثة
        """
        session = get_object_or_404(WhatsAppSession, id=session_id)
        
        return Response({
            'session_id': session.id,
            'phone': session.phone_number,
            'user_id': session.user.id if session.user else None,
            'conversation': session.conversation_history or [],
            'created_at': session.created_at,
            'updated_at': session.updated_at
        })


class ChatResetAPIView(APIView):
    """
    API لإعادة تعيين المحادثة
    """
    
    def post(self, request, session_id):
        """
        إعادة تعيين المحادثة
        """
        session = get_object_or_404(WhatsAppSession, id=session_id)
        session.conversation_history = []
        session.save()
        
        return Response({
            'message': 'تم إعادة تعيين المحادثة بنجاح',
            'session_id': session.id
        })


class CustomerDataAPIView(APIView):
    """
    API لاسترجاع بيانات العميل
    """
    
    def get(self, request):
        """
        الحصول على بيانات العميل
        
        Query params:
        - phone: رقم الجوال
        - national_id: رقم الهوية
        """
        from .customer_data_service import customer_data_service
        
        phone = request.query_params.get('phone')
        national_id = request.query_params.get('national_id')
        
        if not phone and not national_id:
            return Response({
                'error': 'يجب توفير رقم الجوال أو رقم الهوية'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # جلب السجل الكامل
            history = customer_data_service.get_full_customer_history(
                phone=phone,
                national_id=national_id
            )
            
            return Response({
                'success': True,
                'data': history
            })
            
        except Exception as e:
            logger.exception(f"Error getting customer data: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """
        حذف مسودة العميل
        
        Body:
        {
            "phone": "0501234567"
        }
        """
        from .customer_data_service import customer_data_service
        
        phone = request.data.get('phone')
        
        if not phone:
            return Response({
                'error': 'رقم الجوال مطلوب'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            success = customer_data_service.clear_draft(phone)
            
            return Response({
                'success': success,
                'message': 'تم حذف المسودة بنجاح' if success else 'لم يتم العثور على مسودة'
            })
            
        except Exception as e:
            logger.exception(f"Error deleting draft: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class InvoicePDFView(APIView):
    """
    API لتحميل فاتورة PDF
    """
    
    def get(self, request, invoice_id):
        """
        تحميل فاتورة PDF
        """
        from django.http import FileResponse, HttpResponse
        from insurance_core.models import Invoice
        from .pdf_generator import pdf_generator
        from pathlib import Path
        
        try:
            # جلب الفاتورة من قاعدة البيانات
            invoice = get_object_or_404(Invoice, id=invoice_id)
            
            # تحضير بيانات الفاتورة من العلاقات
            order = invoice.order
            user = order.user if order else None
            vehicle = order.vehicle if order else None
            offer = order.offer if order else None
            company = offer.company if offer else None
            
            invoice_data = {
                'invoice_id': invoice.invoice_no,
                'order_code': order.order_code if order else '',
                'national_id': user.national_id if user else '',
                'birth_date': str(user.birth_date) if user and user.birth_date else '',
                'phone': user.phone if user else '',
                'vehicle_brand': vehicle.brand if vehicle else '',
                'vehicle_model': vehicle.model if vehicle else '',
                'vehicle_year': vehicle.model_year if vehicle else '',
                'plate_no': vehicle.plate_no if vehicle else '',
                'vehicle_value': float(vehicle.vehicle_value) if vehicle and vehicle.vehicle_value else 0,
                'coverage_type': offer.get_coverage_type_display() if offer else 'شامل',
                'company_name': company.name_ar if company else '',
                'total_amount': float(invoice.amount),
            }
            
            # توليد PDF
            pdf_path = pdf_generator.save_invoice_html(invoice_data)
            
            # التحقق من وجود الملف
            pdf_file = Path(pdf_path)
            if pdf_file.exists():
                # إرجاع الملف
                if pdf_path.endswith('.pdf'):
                    response = FileResponse(
                        open(pdf_path, 'rb'),
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_no}.pdf"'
                else:
                    # HTML fallback
                    response = FileResponse(
                        open(pdf_path, 'rb'),
                        content_type='text/html'
                    )
                    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_no}.html"'
                return response
            else:
                return Response({
                    'error': 'فشل في توليد الفاتورة'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Invoice.DoesNotExist:
            return Response({
                'error': 'الفاتورة غير موجودة'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Error generating invoice PDF: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PolicyPDFView(APIView):
    """
    API لتحميل وثيقة التأمين PDF
    """
    
    def get(self, request, policy_id):
        """
        تحميل وثيقة التأمين PDF
        """
        from django.http import FileResponse, HttpResponse
        from insurance_core.models import Policy
        from .pdf_generator import pdf_generator
        from pathlib import Path
        
        try:
            # جلب الوثيقة من قاعدة البيانات
            policy = get_object_or_404(Policy, id=policy_id)
            
            # تحضير بيانات الوثيقة
            order = policy.order
            user = order.user if order else None
            vehicle = order.vehicle if order else None
            company = order.offer.company if order and order.offer else None
            
            policy_data = {
                'policy_id': policy.policy_no,
                'invoice_id': order.invoice.invoice_no if order and hasattr(order, 'invoice') and order.invoice else '',
                'national_id': user.national_id if user else '',
                'birth_date': user.birth_date.isoformat() if user and user.birth_date else '',
                'phone': user.phone if user else '',
                'vehicle_brand': vehicle.brand if vehicle else '',
                'vehicle_model': vehicle.model if vehicle else '',
                'vehicle_year': vehicle.model_year if vehicle else '',
                'plate_no': vehicle.plate_no if vehicle else '',
                'vehicle_value': float(vehicle.vehicle_value) if vehicle and vehicle.vehicle_value else 0,
                'coverage_type': order.offer.coverage_type if order and order.offer else 'شامل',
                'company_name': company.name_ar if company else '',
                'total_amount': float(order.total_price) if order and order.total_price else 0,
                'offer_code': order.offer.offer_code if order and order.offer else '',
            }
            
            # توليد PDF
            pdf_path = pdf_generator.save_policy_html(policy_data)
            
            # التحقق من وجود الملف
            pdf_file = Path(pdf_path)
            if pdf_file.exists():
                # إرجاع الملف
                if pdf_path.endswith('.pdf'):
                    response = FileResponse(
                        open(pdf_path, 'rb'),
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = f'attachment; filename="policy_{policy.policy_no}.pdf"'
                else:
                    # HTML fallback
                    response = FileResponse(
                        open(pdf_path, 'rb'),
                        content_type='text/html'
                    )
                    response['Content-Disposition'] = f'attachment; filename="policy_{policy.policy_no}.html"'
                return response
            else:
                return Response({
                    'error': 'فشل في توليد الوثيقة'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Policy.DoesNotExist:
            return Response({
                'error': 'الوثيقة غير موجودة'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Error generating policy PDF: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
