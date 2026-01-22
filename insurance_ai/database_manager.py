"""
SAIA Insurance - Database Manager
مدير قاعدة البيانات - إدارة كاملة للمستخدمين، السيارات، الطلبات، الفواتير، والوثائق
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth import get_user_model

from insurance_core.models import (
    User, Vehicle, InsuranceCompany, InsuranceService,
    InsuranceOffer, InsuranceOrder, Invoice, Payment, Policy
)

logger = logging.getLogger(__name__)

User = get_user_model()


class DatabaseManager:
    """مدير قاعدة البيانات - CRUD كامل"""
    
    # ==================== Users ====================
    
    @staticmethod
    def get_or_create_user(
        national_id: str,
        phone: str,
        birth_date: str,
        first_name: str = "عميل",
        last_name: str = "جديد",
        city: str = "الرياض"
    ) -> Tuple[User, bool]:
        """الحصول على أو إنشاء مستخدم"""
        try:
            # البحث بالهوية أو الجوال
            user = User.objects.filter(
                models.Q(national_id=national_id) | models.Q(phone=phone)
            ).first()
            
            if user:
                logger.info(f"✅ User found: {user.user_code}")
                return user, False
            
            # تحويل تاريخ الميلاد
            if isinstance(birth_date, str):
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            
            # إنشاء مستخدم جديد
            username = f"user_{national_id}"
            user = User.objects.create(
                username=username,
                national_id=national_id,
                phone=phone,
                birth_date=birth_date,
                first_name=first_name,
                last_name=last_name,
                city=city
            )
            
            logger.info(f"✅ User created: {user.user_code}")
            return user, True
            
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            raise
    
    @staticmethod
    def update_user(user: User, **kwargs) -> User:
        """تحديث بيانات المستخدم"""
        try:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.save()
            logger.info(f"✅ User updated: {user.user_code}")
            return user
        except Exception as e:
            logger.error(f"❌ Error updating user: {e}")
            raise
    
    # ==================== Vehicles ====================
    
    @staticmethod
    def get_or_create_vehicle(
        user: User,
        plate_no: str,
        brand: str,
        model: str,
        model_year: int,
        vehicle_value: Decimal
    ) -> Tuple[Vehicle, bool]:
        """الحصول على أو إنشاء مركبة"""
        try:
            # البحث باللوحة
            vehicle = Vehicle.objects.filter(plate_no=plate_no).first()
            
            if vehicle:
                # تحديث البيانات إذا تغيرت
                updated = False
                if vehicle.brand != brand:
                    vehicle.brand = brand
                    updated = True
                if vehicle.model != model:
                    vehicle.model = model
                    updated = True
                if vehicle.model_year != model_year:
                    vehicle.model_year = model_year
                    updated = True
                if vehicle.vehicle_value != vehicle_value:
                    vehicle.vehicle_value = vehicle_value
                    updated = True
                
                if updated:
                    vehicle.save()
                    logger.info(f"✅ Vehicle updated: {vehicle.plate_no}")
                else:
                    logger.info(f"✅ Vehicle found: {vehicle.plate_no}")
                
                return vehicle, False
            
            # إنشاء مركبة جديدة
            vehicle = Vehicle.objects.create(
                user=user,
                plate_no=plate_no,
                brand=brand,
                model=model,
                model_year=model_year,
                vehicle_value=vehicle_value
            )
            
            logger.info(f"✅ Vehicle created: {vehicle.plate_no}")
            return vehicle, True
            
        except Exception as e:
            logger.error(f"❌ Error creating vehicle: {e}")
            raise
    
    # ==================== Insurance Services ====================
    
    @staticmethod
    def get_insurance_services() -> List[Dict]:
        """جلب خدمات التأمين المتاحة"""
        try:
            services = InsuranceService.objects.filter(is_active=True).values(
                'id', 'service_code', 'name_ar', 'name_en',
                'service_type', 'description'
            )
            result = list(services)
            logger.info(f"✅ Found {len(result)} insurance services")
            return result
        except Exception as e:
            logger.error(f"❌ Error fetching services: {e}")
            return []
    
    # ==================== Offers ====================
    
    @staticmethod
    def get_offers(
        service_type: str = 'comprehensive',
        user_age: Optional[int] = None,
        vehicle_year: Optional[int] = None,
        vehicle_value: Optional[Decimal] = None,
        limit: int = 10
    ) -> List[InsuranceOffer]:
        """جلب العروض المتاحة مع الفلترة - عرض واحد لكل شركة"""
        try:
            queryset = InsuranceOffer.objects.filter(
                is_active=True,
                coverage_type=service_type
            ).select_related('company', 'service')
            
            # فلترة حسب العمر
            if user_age:
                queryset = queryset.filter(
                    min_age__lte=user_age,
                    max_age__gte=user_age
                )
            
            # فلترة حسب سنة المركبة
            if vehicle_year:
                queryset = queryset.filter(
                    min_vehicle_year__lte=vehicle_year
                )
            
            # فلترة حسب قيمة المركبة
            if vehicle_value:
                queryset = queryset.filter(
                    models.Q(max_vehicle_value__isnull=True) |
                    models.Q(max_vehicle_value__gte=vehicle_value)
                )
            
            # 🆕 جلب أفضل عرض من كل شركة (الأرخص)
            # نستخدم distinct على company_id ونأخذ الأرخص
            all_offers = list(queryset.order_by('company_id', 'price_base'))
            
            # تصفية للحصول على عرض واحد لكل شركة
            seen_companies = set()
            unique_offers = []
            for offer in all_offers:
                if offer.company_id not in seen_companies:
                    seen_companies.add(offer.company_id)
                    unique_offers.append(offer)
            
            # ترتيب حسب السعر
            unique_offers.sort(key=lambda x: x.price_base)
            
            # تحديد العدد المطلوب
            offers = unique_offers[:limit]
            
            logger.info(f"✅ Found {len(offers)} unique offers from different companies")
            return offers
            
        except Exception as e:
            logger.error(f"❌ Error fetching offers: {e}")
            return []
    
    @staticmethod
    def format_offer_for_display(offer: InsuranceOffer, has_njm: bool = False) -> Dict:
        """تنسيق العرض للعرض"""
        try:
            pricing = offer.calculate_final_price(has_njm)
            
            return {
                'id': offer.id,
                'offer_code': offer.offer_code,
                'company': offer.company.name_ar,
                'company_rating': float(offer.company.rating_score),
                'service': offer.service.name_ar,
                'coverage_type': offer.get_coverage_type_display(),
                'base_price': pricing['base_price'],
                'discount': pricing['discount'],
                'price_after_discount': pricing['price_after_discount'],
                'vat': pricing['vat'],
                'final_price': pricing['final_price'],
                'total_premium': pricing['final_price'],  # 🆕 إضافة total_premium
                'price': pricing['final_price'],  # 🆕 إضافة price كـ fallback
                'gross_premium': pricing['base_price'],  # 🆕 إضافة gross_premium
                'premium_exc_vat': pricing['price_after_discount'],  # 🆕 إضافة premium_exc_vat
                'vat_amount': pricing['vat'],  # 🆕 إضافة vat_amount
                'vat_percent': 15.0,  # 🆕 إضافة vat_percent
                'ncd_discount_amount': pricing['discount'],  # 🆕 إضافة ncd_discount_amount
                'ncd_discount_percent': float(offer.njm_discount_pct) if pricing['discount'] > 0 else 0,  # 🆕
                'deductible_options': offer.deductible_options,
                'included_features': offer.included_features_json,
                'optional_addons': offer.optional_addons_json,
                'min_age': offer.min_age,
                'max_age': offer.max_age,
                'min_vehicle_year': offer.min_vehicle_year,
            }
        except Exception as e:
            logger.error(f"❌ Error formatting offer: {e}")
            return {}
    
    # ==================== Orders ====================
    
    @staticmethod
    @transaction.atomic
    def create_order(
        user: User,
        offer: InsuranceOffer,
        vehicle: Vehicle,
        has_njm_discount: bool = False,
        selected_deductible: Optional[Dict] = None,
        selected_addons: Optional[List] = None
    ) -> InsuranceOrder:
        """إنشاء طلب تأمين"""
        try:
            # حساب السعر النهائي
            pricing = offer.calculate_final_price(has_njm_discount)
            total_price = Decimal(str(pricing['final_price']))
            
            # إضافة سعر الإضافات
            if selected_addons:
                for addon in selected_addons:
                    if 'price' in addon:
                        total_price += Decimal(str(addon['price']))
            
            # إنشاء الطلب
            order = InsuranceOrder.objects.create(
                user=user,
                offer=offer,
                vehicle=vehicle,
                total_price=total_price,
                status='awaiting_confirmation',
                has_njm_discount=has_njm_discount,
                selected_deductible=selected_deductible or {},
                selected_addons=selected_addons or []
            )
            
            logger.info(f"✅ Order created: {order.order_code}")
            return order
            
        except Exception as e:
            logger.error(f"❌ Error creating order: {e}")
            raise
    
    @staticmethod
    def update_order_status(order: InsuranceOrder, status: str) -> InsuranceOrder:
        """تحديث حالة الطلب"""
        try:
            order.status = status
            order.save()
            logger.info(f"✅ Order {order.order_code} status updated to: {status}")
            return order
        except Exception as e:
            logger.error(f"❌ Error updating order status: {e}")
            raise
    
    # ==================== Invoices ====================
    
    @staticmethod
    @transaction.atomic
    def create_invoice(order: InsuranceOrder, expires_hours: int = 24) -> Invoice:
        """إنشاء فاتورة"""
        try:
            # التحقق من عدم وجود فاتورة
            if hasattr(order, 'invoice'):
                logger.info(f"✅ Invoice already exists: {order.invoice.invoice_no}")
                return order.invoice
            
            # حساب تاريخ الانتهاء
            expires_at = timezone.now() + timedelta(hours=expires_hours)
            
            # إنشاء الفاتورة
            invoice = Invoice.objects.create(
                order=order,
                amount=order.total_price,
                status='pending',
                expires_at=expires_at
            )
            
            # تحديث حالة الطلب
            order.status = 'pending_payment'
            order.save()
            
            logger.info(f"✅ Invoice created: {invoice.invoice_no}")
            return invoice
            
        except Exception as e:
            logger.error(f"❌ Error creating invoice: {e}")
            raise
    
    # ==================== Payments ====================
    
    @staticmethod
    @transaction.atomic
    def process_payment(
        invoice: Invoice,
        payment_method: str = 'credit_card',
        transaction_ref: Optional[str] = None
    ) -> Payment:
        """معالجة الدفع"""
        try:
            import uuid
            
            # إنشاء رقم معاملة
            if not transaction_ref:
                transaction_ref = f"TXN{uuid.uuid4().hex[:12].upper()}"
            
            # إنشاء الدفعة
            payment = Payment.objects.create(
                invoice=invoice,
                transaction_ref=transaction_ref,
                amount=invoice.amount,
                payment_method=payment_method,
                status='completed',  # في الإنتاج: pending ثم completed بعد التأكيد
                completed_at=timezone.now()
            )
            
            # تحديث الفاتورة
            invoice.status = 'paid'
            invoice.paid_at = timezone.now()
            invoice.save()
            
            # تحديث الطلب
            order = invoice.order
            order.status = 'paid'
            order.save()
            
            logger.info(f"✅ Payment processed: {payment.transaction_ref}")
            return payment
            
        except Exception as e:
            logger.error(f"❌ Error processing payment: {e}")
            raise
    
    # ==================== Policies ====================
    
    @staticmethod
    @transaction.atomic
    def issue_policy(order: InsuranceOrder) -> Policy:
        """إصدار وثيقة التأمين"""
        try:
            # التحقق من عدم وجود وثيقة
            if hasattr(order, 'policy'):
                logger.info(f"✅ Policy already exists: {order.policy.policy_no}")
                return order.policy
            
            # تحديد تواريخ الوثيقة
            start_date = date.today()
            end_date = start_date + timedelta(days=365)  # سنة واحدة
            
            # إنشاء الوثيقة أولاً للحصول على ID
            policy = Policy.objects.create(
                order=order,
                start_date=start_date,
                end_date=end_date,
                pdf_url=""  # سيتم تحديثه
            )
            
            # بناء رابط PDF الصحيح
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
            pdf_url = f"{base_url}/api/ai/policies/{policy.id}/pdf/"
            
            # تحديث رابط PDF
            policy.pdf_url = pdf_url
            policy.save()
            
            # تحديث حالة الطلب
            order.status = 'policy_issued'
            order.save()
            
            logger.info(f"✅ Policy issued: {policy.policy_no} - URL: {pdf_url}")
            return policy
            
        except Exception as e:
            logger.error(f"❌ Error issuing policy: {e}")
            raise
    
    # ==================== Complete Flow ====================
    
    @staticmethod
    @transaction.atomic
    def complete_insurance_flow(
        national_id: str,
        phone: str,
        birth_date: str,
        plate_no: str,
        brand: str,
        model: str,
        model_year: int,
        vehicle_value: Decimal,
        offer_id: int,
        has_njm_discount: bool = False,
        payment_method: str = 'credit_card'
    ) -> Dict[str, Any]:
        """تنفيذ التدفق الكامل: مستخدم → مركبة → طلب → فاتورة → دفع → وثيقة"""
        try:
            logger.info("🚀 Starting complete insurance flow...")
            
            # 1. إنشاء/جلب المستخدم
            user, user_created = DatabaseManager.get_or_create_user(
                national_id=national_id,
                phone=phone,
                birth_date=birth_date
            )
            
            # 2. إنشاء/جلب المركبة
            vehicle, vehicle_created = DatabaseManager.get_or_create_vehicle(
                user=user,
                plate_no=plate_no,
                brand=brand,
                model=model,
                model_year=model_year,
                vehicle_value=vehicle_value
            )
            
            # 3. جلب العرض
            offer = InsuranceOffer.objects.get(id=offer_id)
            
            # 4. إنشاء الطلب
            order = DatabaseManager.create_order(
                user=user,
                offer=offer,
                vehicle=vehicle,
                has_njm_discount=has_njm_discount
            )
            
            # 5. إنشاء الفاتورة
            invoice = DatabaseManager.create_invoice(order)
            
            # 6. معالجة الدفع
            payment = DatabaseManager.process_payment(invoice, payment_method)
            
            # 7. إصدار الوثيقة
            policy = DatabaseManager.issue_policy(order)
            
            logger.info("✅ Complete insurance flow finished successfully!")
            
            return {
                'success': True,
                'user': {
                    'user_code': user.user_code,
                    'name': user.get_full_name(),
                    'created': user_created
                },
                'vehicle': {
                    'plate_no': vehicle.plate_no,
                    'description': str(vehicle),
                    'created': vehicle_created
                },
                'order': {
                    'order_code': order.order_code,
                    'total_price': float(order.total_price),
                    'status': order.status
                },
                'invoice': {
                    'invoice_no': invoice.invoice_no,
                    'amount': float(invoice.amount),
                    'status': invoice.status
                },
                'payment': {
                    'transaction_ref': payment.transaction_ref,
                    'status': payment.status
                },
                'policy': {
                    'policy_no': policy.policy_no,
                    'start_date': policy.start_date.isoformat(),
                    'end_date': policy.end_date.isoformat(),
                    'pdf_url': policy.pdf_url
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error in complete flow: {e}")
            raise


# ==================== Singleton Instance ====================

database_manager = DatabaseManager()
