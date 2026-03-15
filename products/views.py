from rest_framework import viewsets, permissions, filters, parsers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from .models import Product, SupplierProduct, ProductImage, PurchaseOrder, StockLedger, SupplierPayment
from .serializers import (
    ProductSerializer, SupplierProductSerializer, ProductImageSerializer, 
    PurchaseOrderSerializer, ProductDetailSerializer,
    StockLedgerSerializer, SupplierPaymentSerializer
)
from .permissions import (
    IsAdmin, IsSupplier, IsCustomer, IsSupplierOwner,
    CanApproveProduct, CanCreatePurchaseOrder, CanPlaceOrder
)
from suppliers.models import Supplier
import uuid


class SupplierProductViewSet(viewsets.ModelViewSet):
    queryset = SupplierProduct.objects.all()
    serializer_class = SupplierProductSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['create', 'my_products']:
            return [IsSupplier()]
        elif self.action in ['approve', 'reject']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return SupplierProduct.objects.none()
            
        base_qs = SupplierProduct.objects.all()
        
        if user.role == 'ADMIN':
            return base_qs
        if user.role == 'SUPPLIER':
            return base_qs.filter(supplier_id=user.id)
        
        # Customers and others see nothing
        return SupplierProduct.objects.none()

    def perform_create(self, serializer):
        # Check if supplier is verified
        from suppliers.models import Supplier
        
        # If user is admin, allow them to act as a supplier for testing or manual entries
        if self.request.user.role == 'ADMIN':
            # Create a verified supplier profile for the admin if it doesn't exist
            Supplier.objects.get_or_create(
                user=self.request.user,
                defaults={
                    'company_name': f"Admin Store ({self.request.user.name or self.request.user.email})",
                    'is_verified': True
                }
            )
            serializer.save(supplier=self.request.user)
            return

        # For normal suppliers, ensure they have a profile and are verified
        supplier_profile, created = Supplier.objects.get_or_create(
            user=self.request.user,
            defaults={'company_name': self.request.user.name or self.request.user.email}
        )
        
        if not supplier_profile.is_verified:
            raise PermissionDenied("Your supplier account must be verified by admin before submitting products.")
            
        serializer.save(supplier=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status == 'APPROVED' and self.request.user.role == 'SUPPLIER':
            raise PermissionDenied("Approved products cannot be modified by suppliers.")
            
        # Check if supplier is verified
        from suppliers.models import Supplier
        supplier_profile = Supplier.objects.filter(user_id=self.request.user.id).first()
        
        # Admin can always update
        if self.request.user.role != 'ADMIN':
            if not supplier_profile or not supplier_profile.is_verified:
                raise PermissionDenied("Your account must be verified by admin before submitting products.")
            
        instance = serializer.save()
        if instance.status == 'REJECTED':
            instance.status = 'PENDING'
            instance.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        supplier_product = self.get_object()
        # Allow passing selling_price, or default to suggested_retail_price
        selling_price = request.data.get('selling_price') or supplier_product.suggested_retail_price
        
        if not selling_price or float(selling_price) <= 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid selling price for approval: {selling_price}")
            return Response({'error': 'A valid selling price is required for approval'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .services import ProductService
            product = ProductService.approve_supplier_product(supplier_product.id, selling_price)
            return Response({'status': 'approved', 'product_id': str(product.id)})
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Product approval failed:")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        supplier_product = self.get_object()
        supplier_product.status = 'REJECTED'
        supplier_product.admin_notes = request.data.get('notes', '')
        supplier_product.save()
        return Response({'status': 'rejected'})

    @action(detail=False, methods=['get'])
    def my_products(self, request):
        products = SupplierProduct.objects.filter(supplier_id=request.user.id).prefetch_related('images')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('category', 'supplier').prefetch_related('images')
    serializer_class = ProductSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'category', 'purity', 'is_featured', 'is_approved']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['selling_price', 'created_at']

    def get_permissions(self):
        if self.action in ['create']:
            return [IsSupplier()]
        elif self.action in ['approve_product', 'set_selling_price']:
            return [IsAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsSupplierOwner()]
        elif self.action == 'my_products':
            return [IsSupplier()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        base_queryset = Product.objects.all()
        
        if self.request.user.is_authenticated:
            if self.request.user.role == 'ADMIN':
                return base_queryset
            elif self.request.user.role == 'SUPPLIER':
                return base_queryset.filter(supplier_user_id=self.request.user.id)
            elif self.request.user.role == 'CUSTOMER':
                return base_queryset.filter(is_approved=True, is_available_for_sale=True, stock_quantity__gt=0)
        return base_queryset.filter(is_approved=True, is_available_for_sale=True, stock_quantity__gt=0)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        serializer.save(supplier_user=self.request.user)
    
    def perform_update(self, serializer):
        product = self.get_object()
        if self.request.user.role == 'SUPPLIER' and product.supplier_user != self.request.user:
            raise PermissionDenied("You can only edit your own products")
        serializer.save()
    
    def perform_destroy(self, instance):
        if self.request.user.role == 'SUPPLIER' and instance.supplier_user != self.request.user:
            raise PermissionDenied("You can only delete your own products")
        instance.delete()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin()])
    def approve_product(self, request, pk=None):
        product = self.get_object()
        product.is_approved = True
        product.save()
        return Response({'status': 'Product approved'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin()])
    def set_selling_price(self, request, pk=None):
        product = self.get_object()
        selling_price = request.data.get('selling_price')
        
        if selling_price is None:
            return Response(
                {'error': 'selling_price is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.selling_price = selling_price
        product.save()
        return Response(
            {'status': 'Selling price updated', 'selling_price': float(product.selling_price)},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsSupplier()])
    def my_products(self, request):
        products = Product.objects.filter(supplier_user_id=request.user.id).prefetch_related('images')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'supplier']
    ordering_fields = ['created_at', '-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'approve_order', 'mark_received']:
            return [IsAdmin()]
        elif self.action == 'supplier_orders':
            return [IsSupplier()]
        return [IsAdmin()]
    
    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return PurchaseOrder.objects.none()
            
        base_qs = PurchaseOrder.objects.all().select_related('supplier', 'product')
        
        if user.role == 'ADMIN':
            return base_qs
        elif user.role == 'SUPPLIER':
            return base_qs.filter(supplier=user)
            
        # Customers see nothing
        return PurchaseOrder.objects.none()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_received(self, request, pk=None):
        purchase_order = self.get_object()
        if purchase_order.status == 'RECEIVED':
            return Response({'error': 'Already received'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            from .services import StockService
            StockService.receive_purchase_order(purchase_order.id)
            return Response({'status': 'Purchase order marked as received'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def supplier_orders(self, request):
        orders = PurchaseOrder.objects.filter(supplier=request.user)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class StockLedgerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockLedger.objects.all().select_related('product')
    serializer_class = StockLedgerSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'entry_type']
    ordering_fields = ['created_at']


class SupplierPaymentViewSet(viewsets.ModelViewSet):
    queryset = SupplierPayment.objects.all().select_related('purchase_order', 'purchase_order__supplier')
    serializer_class = SupplierPaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['purchase_order', 'payment_method']
    ordering_fields = ['payment_date', '-payment_date']

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        base_qs = SupplierPayment.objects.all().select_related('purchase_order', 'purchase_order__supplier')
        
        if not user.is_authenticated:
            return SupplierPayment.objects.none()
        if user.role == 'ADMIN':
            return base_qs
        elif user.role == 'SUPPLIER':
            return base_qs.filter(purchase_order__supplier=user)
        return SupplierPayment.objects.none()

    @action(detail=False, methods=['get'], url_path=r'by-po/(?P<po_id>[\w-]+)')
    def by_po(self, request, po_id=None):
        payments = self.get_queryset().filter(purchase_order_id=po_id)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
