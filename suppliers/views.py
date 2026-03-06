from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Supplier
from .serializers import SupplierSerializer
from products.models import Product, SupplierProduct
from orders.models import OrderItem
from django.db.models import Sum

class SupplierProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = SupplierSerializer

    def get_queryset(self):
        return Supplier.objects.filter(user=self.request.user)

    def get_object(self):
        obj, created = Supplier.objects.get_or_create(user=self.request.user)
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
