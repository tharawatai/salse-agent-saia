"""
Serializers لتحويل Models إلى JSON
"""
from rest_framework import serializers
from .models import (
    User, Vehicle, InsuranceCompany, InsuranceService,
    InsuranceOffer, InsuranceOrder, Invoice, Payment, Policy
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer للمستخدم"""
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'national_id', 'first_name', 'last_name',
            'birth_date', 'age', 'phone', 'city', 'email', 'user_code'
        ]
        read_only_fields = ['user_code']


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer للمركبة"""
    age = serializers.ReadOnlyField()
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'user', 'user_name', 'plate_no', 'brand', 'model',
            'model_year', 'age', 'vehicle_value', 'created_at'
        ]


class InsuranceCompanySerializer(serializers.ModelSerializer):
    """Serializer لشركة التأمين"""
    
    class Meta:
        model = InsuranceCompany
        fields = [
            'id', 'company_code', 'name_ar', 'name_en',
            'rating_score'
        ]


class InsuranceServiceSerializer(serializers.ModelSerializer):
    """Serializer للخدمة"""
    
    class Meta:
        model = InsuranceService
        fields = [
            'id', 'service_code', 'name_ar', 'name_en',
            'service_type', 'description'
        ]


class InsuranceOfferSerializer(serializers.ModelSerializer):
    """Serializer للعرض"""
    company_name = serializers.CharField(source='company.name_ar', read_only=True)
    service_name = serializers.CharField(source='service.name_ar', read_only=True)
    final_price = serializers.SerializerMethodField()
    
    class Meta:
        model = InsuranceOffer
        fields = [
            'id', 'company', 'company_name', 'service', 'service_name',
            'offer_code', 'coverage_type', 'price_base', 'final_price',
            'min_age', 'max_age', 'min_vehicle_year',
            'included_features_json'
        ]
    
    def get_final_price(self, obj):
        """حساب السعر النهائي"""
        pricing = obj.calculate_final_price()
        return pricing


class InsuranceOrderSerializer(serializers.ModelSerializer):
    """Serializer للطلب"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    offer_details = InsuranceOfferSerializer(source='offer', read_only=True)
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    
    class Meta:
        model = InsuranceOrder
        fields = [
            'id', 'user', 'user_name', 'offer', 'offer_details',
            'vehicle', 'vehicle_details', 'order_code', 'status',
            'total_price', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_code']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer للفاتورة"""
    order_details = InsuranceOrderSerializer(source='order', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'order', 'order_details', 'invoice_no', 'amount',
            'status', 'issued_at', 'expires_at', 'paid_at'
        ]
        read_only_fields = ['invoice_no']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer للدفع"""
    invoice_details = InvoiceSerializer(source='invoice', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_details', 'transaction_ref',
            'gateway', 'amount', 'status', 'payment_method',
            'paid_at', 'created_at'
        ]


class PolicySerializer(serializers.ModelSerializer):
    """Serializer للوثيقة"""
    order_details = InsuranceOrderSerializer(source='order', read_only=True)
    
    class Meta:
        model = Policy
        fields = [
            'id', 'order', 'order_details', 'policy_no',
            'start_date', 'end_date', 'policy_file',
            'issued_at', 'is_active'
        ]
        read_only_fields = ['policy_no']


class CreateOrderSerializer(serializers.Serializer):
    """Serializer لإنشاء طلب جديد"""
    user_id = serializers.IntegerField()
    offer_id = serializers.IntegerField()
    vehicle_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """التحقق من البيانات"""
        # التحقق من المستخدم
        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'المستخدم غير موجود'})
        
        # التحقق من العرض
        try:
            offer = InsuranceOffer.objects.get(id=data['offer_id'])
        except InsuranceOffer.DoesNotExist:
            raise serializers.ValidationError({'offer_id': 'العرض غير موجود'})
        
        # التحقق من المركبة
        try:
            vehicle = Vehicle.objects.get(id=data['vehicle_id'], user=user)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError({'vehicle_id': 'المركبة غير موجودة أو لا تنتمي للمستخدم'})
        
        # التحقق من العمر
        if user.age < offer.min_age or user.age > offer.max_age:
            raise serializers.ValidationError({
                'user_id': f'عمر المستخدم يجب أن يكون بين {offer.min_age} و {offer.max_age}'
            })
        
        # التحقق من سنة المركبة
        if vehicle.model_year < offer.min_vehicle_year:
            raise serializers.ValidationError({
                'vehicle_id': f'سنة المركبة يجب أن تكون {offer.min_vehicle_year} أو أحدث'
            })
        
        data['user'] = user
        data['offer'] = offer
        data['vehicle'] = vehicle
        
        return data
    
    def create(self, validated_data):
        """إنشاء الطلب"""
        user = validated_data['user']
        offer = validated_data['offer']
        vehicle = validated_data['vehicle']
        notes = validated_data.get('notes', '')
        
        # حساب السعر النهائي
        pricing = offer.calculate_final_price()
        
        # إنشاء الطلب
        order = InsuranceOrder.objects.create(
            user=user,
            offer=offer,
            vehicle=vehicle,
            total_price=pricing['final_price'],
            notes=notes,
            status='awaiting_confirmation'
        )
        
        return order


class SearchOffersSerializer(serializers.Serializer):
    """Serializer للبحث عن العروض"""
    user_age = serializers.IntegerField(required=False)
    vehicle_year = serializers.IntegerField(required=False)
    coverage_type = serializers.ChoiceField(
        choices=['comprehensive', 'third_party'],
        required=False
    )
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    company_id = serializers.IntegerField(required=False)
