from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    UserProfileView, 
    AdminUserListView, 
    AdminUserDeleteView,
    AdminSupplierListView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<str:pk>/', AdminUserDeleteView.as_view(), name='admin_user_delete'),
    path('admin/suppliers/', AdminSupplierListView.as_view(), name='admin_supplier_list'),
]
