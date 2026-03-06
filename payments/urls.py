from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet
from products.views import SupplierPaymentViewSet

router = DefaultRouter()
router.register(r'supplier', SupplierPaymentViewSet, basename='supplierpayment')
router.register(r'', PaymentViewSet, basename='payments')

urlpatterns = [
    path('by-po/<int:po_id>/', SupplierPaymentViewSet.as_view({'get': 'by_po'}), name='payments-by-po'),
    path('', include(router.urls)),
]
