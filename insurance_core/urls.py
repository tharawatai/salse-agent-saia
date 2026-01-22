from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'insurance_core'

# إنشاء Router للـ ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'vehicles', views.VehicleViewSet, basename='vehicle')
router.register(r'companies', views.InsuranceCompanyViewSet, basename='company')
router.register(r'services', views.InsuranceServiceViewSet, basename='service')
router.register(r'offers', views.InsuranceOfferViewSet, basename='offer')
router.register(r'orders', views.InsuranceOrderViewSet, basename='order')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'policies', views.PolicyViewSet, basename='policy')

urlpatterns = [
    path('', include(router.urls)),
    # PDF Download endpoints
    path('documents/<str:filename>', views.download_document, name='download_document'),
]
