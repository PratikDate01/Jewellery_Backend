from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Supplier
from .serializers import SupplierSerializer
from products.models import Product, SupplierProduct
from orders.models import OrderItem
from django.db.models import Sum

class SupplierProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SupplierSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Supplier.objects.none()
        return Supplier.objects.filter(user=self.request.user)

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise permissions.NotAuthenticated()
        obj, created = Supplier.objects.get_or_create(
            user=self.request.user,
            defaults={'company_name': self.request.user.name or self.request.user.email}
        )
        return obj

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        profile, created = Supplier.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        products = SupplierProduct.objects.filter(supplier=request.user).prefetch_related('images')
        from products.serializers import SupplierProductSerializer
        serializer = SupplierProductSerializer(products, many=True)
        return Response(serializer.data)
