from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierProfileViewSet

router = DefaultRouter()
router.register(r'', SupplierProfileViewSet, basename='supplier')

urlpatterns = [
    path('', include(router.urls)),
]
