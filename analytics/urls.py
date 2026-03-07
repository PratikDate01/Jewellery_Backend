from django.urls import path
from .views import AdminAnalyticsView, WholesalerAnalyticsView, UnifiedDashboardView

urlpatterns = [
    path('admin/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('wholesaler/', WholesalerAnalyticsView.as_view(), name='wholesaler_analytics'),
    path('dashboard/', UnifiedDashboardView.as_view(), name='unified_dashboard'),
]
