from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, SupplierProductViewSet, ProductImageViewSet, 
    PurchaseOrderViewSet, CustomerOrderViewSet, StockLedgerViewSet
)

router = DefaultRouter()
router.register(r'supplier-products', SupplierProductViewSet, basename='supplierproduct')
router.register(r'images', ProductImageViewSet, basename='productimage')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'customer-orders', CustomerOrderViewSet, basename='customerorder')
router.register(r'stock-ledger', StockLedgerViewSet, basename='stockledger')
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]
