from django.urls import path
from .views import AdminAnalyticsView, UnifiedDashboardView

urlpatterns = [
    path('admin/', AdminAnalyticsView.as_view(), name='admin_analytics'),
    path('dashboard/', UnifiedDashboardView.as_view(), name='unified_dashboard'),
]
