from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WholesaleProfileViewSet, NegotiationRequestViewSet

router = DefaultRouter()
router.register(r'profile', WholesaleProfileViewSet, basename='wholesale-profile')
router.register(r'negotiations', NegotiationRequestViewSet, basename='negotiation')

urlpatterns = [
    path('', include(router.urls)),
]
