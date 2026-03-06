from django.urls import path
from .views import AdminAnalyticsView, WholesalerAnalyticsView, SupplierAnalyticsView

urlpatterns = [
    path('admin/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('wholesaler/', WholesalerAnalyticsView.as_view(), name='wholesaler_analytics'),
    path('supplier/', SupplierAnalyticsView.as_view(), name='supplier_analytics'),
]
