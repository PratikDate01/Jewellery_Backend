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
        user = self.request.user
        if not user.is_authenticated:
            return Supplier.objects.none()
        
        # Admins can see ALL suppliers
        if user.role == 'ADMIN':
            return Supplier.objects.all()
            
        # Suppliers can only see their own profile
        return Supplier.objects.filter(user=user)

    def get_object(self):
        # If accessing by ID (standard ModelViewSet behavior)
        pk = self.kwargs.get('pk')
        if pk:
            try:
                return Supplier.objects.get(pk=pk)
            except (Supplier.DoesNotExist, ValueError):
                # Fallback to default behavior if PK is invalid
                return super().get_object()
            
        # Fallback for "my-profile" logic
        if not self.request.user.is_authenticated:
            raise permissions.NotAuthenticated()
            
        # Optimization: check exists first before get_or_create to avoid unnecessary writes on every fetch
        profile = Supplier.objects.filter(user=self.request.user).first()
        if not profile:
            profile = Supplier.objects.create(
                user=self.request.user,
                company_name=self.request.user.name or self.request.user.email
            )
        return profile

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify(self, request, pk=None):
        if request.user.role != 'ADMIN':
            return Response({"detail": "Only admins can verify suppliers"}, status=status.HTTP_403_FORBIDDEN)
            
        supplier = self.get_object()
        supplier.is_verified = True
        supplier.save()
        return Response({"status": "verified", "company_name": supplier.company_name})

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
