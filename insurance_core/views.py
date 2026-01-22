"""
API Views للعمليات الأساسية
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import (
    User, Vehicle, InsuranceCompany, InsuranceService,
    InsuranceOffer, InsuranceOrder, Invoice, Payment, Policy
)
from .serializers import (
    UserSerializer, VehicleSerializer, InsuranceCompanySerializer,
    InsuranceServiceSerializer, InsuranceOfferSerializer,
    InsuranceOrderSerializer, InvoiceSerializer, PaymentSerializer,
    PolicySerializer, CreateOrderSerializer, SearchOffersSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """API للمستخدمين"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    @action(detail=True, methods=['get'])
    def vehicles(self, request, pk=None):
        """الحصول على مركبات المستخدم"""
        user = self.get_object()
        vehicles = user.vehicles.all()
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """الحصول على طلبات المستخدم"""
        user = self.get_object()
        orders = user.orders.all().order_by('-created_at')
        serializer = InsuranceOrderSerializer(orders, many=True)
        return Response(serializer.data)


class VehicleViewSet(viewsets.ModelViewSet):
    """API للمركبات"""
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


class InsuranceCompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """API لشركات التأمين (قراءة فقط)"""
    queryset = InsuranceCompany.objects.all()
    serializer_class = InsuranceCompanySerializer


class InsuranceServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """API للخدمات (قراءة فقط)"""
    queryset = InsuranceService.objects.all()
    serializer_class = InsuranceServiceSerializer


class InsuranceOfferViewSet(viewsets.ReadOnlyModelViewSet):
    """API للعروض"""
    queryset = InsuranceOffer.objects.all()
    serializer_class = InsuranceOfferSerializer
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """البحث عن العروض المناسبة"""
        serializer = SearchOffersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # البدء بجميع العروض
        offers = InsuranceOffer.objects.all()
        
        # تطبيق الفلاتر
        if 'user_age' in serializer.validated_data:
            user_age = serializer.validated_data['user_age']
            offers = offers.filter(min_age__lte=user_age, max_age__gte=user_age)
        
        if 'vehicle_year' in serializer.validated_data:
            vehicle_year = serializer.validated_data['vehicle_year']
            offers = offers.filter(min_vehicle_year__lte=vehicle_year)
        
        if 'coverage_type' in serializer.validated_data:
            coverage_type = serializer.validated_data['coverage_type']
            offers = offers.filter(coverage_type=coverage_type)
        
        if 'min_price' in serializer.validated_data:
            min_price = serializer.validated_data['min_price']
            offers = offers.filter(price_base__gte=min_price)
        
        if 'max_price' in serializer.validated_data:
            max_price = serializer.validated_data['max_price']
            offers = offers.filter(price_base__lte=max_price)
        
        if 'company_id' in serializer.validated_data:
            company_id = serializer.validated_data['company_id']
            offers = offers.filter(company_id=company_id)
        
        # ترتيب حسب السعر
        offers = offers.order_by('price_base')
        
        # إرجاع النتائج
        result_serializer = InsuranceOfferSerializer(offers, many=True)
        return Response({
            'count': offers.count(),
            'offers': result_serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def calculate_price(self, request, pk=None):
        """حساب السعر النهائي للعرض"""
        offer = self.get_object()
        has_njm_discount = request.query_params.get('has_njm_discount', 'false').lower() == 'true'
        
        pricing = offer.calculate_final_price(has_njm_discount=has_njm_discount)
        
        return Response({
            'offer_id': offer.id,
            'offer_code': offer.offer_code,
            'company': offer.company.name_ar,
            'service': offer.service.name_ar,
            'pricing': pricing
        })


class InsuranceOrderViewSet(viewsets.ModelViewSet):
    """API للطلبات"""
    queryset = InsuranceOrder.objects.all()
    serializer_class = InsuranceOrderSerializer
    
    def create(self, request):
        """إنشاء طلب جديد"""
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # إنشاء الطلب
        order = serializer.save()
        
        # إنشاء الفاتورة تلقائياً
        invoice = Invoice.objects.create(
            order=order,
            amount=order.total_price,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # إرجاع النتيجة
        order_serializer = InsuranceOrderSerializer(order)
        invoice_serializer = InvoiceSerializer(invoice)
        
        return Response({
            'message': 'تم إنشاء الطلب بنجاح',
            'order': order_serializer.data,
            'invoice': invoice_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """تأكيد الطلب"""
        order = self.get_object()
        
        if order.status != 'awaiting_confirmation':
            return Response({
                'error': 'لا يمكن تأكيد هذا الطلب'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'confirmed'
        order.save()
        
        serializer = InsuranceOrderSerializer(order)
        return Response({
            'message': 'تم تأكيد الطلب بنجاح',
            'order': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """إلغاء الطلب"""
        order = self.get_object()
        
        if order.status in ['completed', 'cancelled']:
            return Response({
                'error': 'لا يمكن إلغاء هذا الطلب'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'cancelled'
        order.save()
        
        serializer = InsuranceOrderSerializer(order)
        return Response({
            'message': 'تم إلغاء الطلب بنجاح',
            'order': serializer.data
        })


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """API للفواتير (قراءة فقط)"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    
    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        """التحقق من حالة الفاتورة"""
        invoice = self.get_object()
        
        is_expired = invoice.expires_at and timezone.now() > invoice.expires_at
        
        return Response({
            'invoice_no': invoice.invoice_no,
            'status': invoice.status,
            'amount': invoice.amount,
            'is_expired': is_expired,
            'expires_at': invoice.expires_at,
            'paid_at': invoice.paid_at
        })


class PaymentViewSet(viewsets.ModelViewSet):
    """API للمدفوعات"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def create(self, request):
        """إنشاء دفعة جديدة"""
        invoice_id = request.data.get('invoice_id')
        gateway = request.data.get('gateway', 'moyasar')
        payment_method = request.data.get('payment_method', 'credit_card')
        
        # الحصول على الفاتورة
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # التحقق من حالة الفاتورة
        if invoice.status == 'paid':
            return Response({
                'error': 'الفاتورة مدفوعة بالفعل'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if invoice.expires_at and timezone.now() > invoice.expires_at:
            return Response({
                'error': 'الفاتورة منتهية الصلاحية'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # إنشاء الدفعة
        payment = Payment.objects.create(
            invoice=invoice,
            transaction_ref=f'TXN{timezone.now().strftime("%Y%m%d%H%M%S")}',
            gateway=gateway,
            amount=invoice.amount,
            payment_method=payment_method,
            status='pending'
        )
        
        # محاكاة الدفع (في الواقع سيتم التكامل مع بوابة الدفع)
        # هنا نفترض أن الدفع نجح
        payment.status = 'completed'
        payment.paid_at = timezone.now()
        payment.save()
        
        # تحديث الفاتورة
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()
        
        # تحديث الطلب
        order = invoice.order
        order.status = 'completed'
        order.save()
        
        # إنشاء الوثيقة
        policy = Policy.objects.create(
            order=order,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=365)).date()
        )
        
        # إرجاع النتيجة
        payment_serializer = PaymentSerializer(payment)
        policy_serializer = PolicySerializer(policy)
        
        return Response({
            'message': 'تم الدفع بنجاح',
            'payment': payment_serializer.data,
            'policy': policy_serializer.data
        }, status=status.HTTP_201_CREATED)


class PolicyViewSet(viewsets.ReadOnlyModelViewSet):
    """API للوثائق (قراءة فقط)"""
    queryset = Policy.objects.all()
    serializer_class = PolicySerializer
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """تحميل الوثيقة"""
        policy = self.get_object()
        
        # في الواقع سيتم إنشاء ملف PDF وإرجاعه
        # هنا نرجع فقط معلومات الوثيقة
        
        return Response({
            'policy_no': policy.policy_no,
            'order': policy.order.order_code,
            'user': policy.order.user.get_full_name(),
            'vehicle': f"{policy.order.vehicle.brand} {policy.order.vehicle.model}",
            'company': policy.order.offer.company.name_ar,
            'service': policy.order.offer.service.name_ar,
            'start_date': policy.start_date,
            'end_date': policy.end_date,
            'message': 'في الإنتاج سيتم إنشاء ملف PDF'
        })


# ============================================
# PDF Download Views
# ============================================

from django.http import FileResponse, Http404
from pathlib import Path
import os

def download_document(request, filename):
    """
    تحميل ملف PDF (فاتورة أو وثيقة)
    """
    # مسار مجلد المستندات
    documents_dir = Path("/tmp/saia_documents")
    file_path = documents_dir / filename
    
    # التحقق من وجود الملف
    if not file_path.exists():
        raise Http404("الملف غير موجود")
    
    # التحقق من أن الملف داخل المجلد المسموح
    if not str(file_path.resolve()).startswith(str(documents_dir.resolve())):
        raise Http404("مسار غير صالح")
    
    # تحديد نوع المحتوى
    content_type = 'application/pdf' if filename.endswith('.pdf') else 'text/html'
    
    # إرجاع الملف
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
