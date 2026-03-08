from rest_framework import viewsets, permissions, filters, parsers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from .models import Product, SupplierProduct, ProductImage, PurchaseOrder, CustomerOrder, StockLedger, SupplierPayment
from .serializers import (
    ProductSerializer, SupplierProductSerializer, ProductImageSerializer, 
    PurchaseOrderSerializer, CustomerOrderSerializer, ProductDetailSerializer,
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
        base_qs = SupplierProduct.objects.all()
        
        if not user or not user.is_authenticated:
            return SupplierProduct.objects.none()
        if user.role == 'ADMIN':
            return base_qs
        return base_qs.filter(supplier_id=user.id)

    def perform_create(self, serializer):
        serializer.save(supplier=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        supplier_product = self.get_object()
        supplier_product.status = 'APPROVED'
        supplier_product.save()
        
        # Create or update store product
        product, created = Product.objects.get_or_create(
            supplier_product=supplier_product,
            defaults={
                'name': supplier_product.name,
                'description': supplier_product.description,
                'category': supplier_product.category,
                'cost_price': supplier_product.cost_price,
                'stock_quantity': 0, # Strict: Start with 0 stock until PurchaseOrder is received
                'purity': supplier_product.purity,
                'gold_weight': supplier_product.gold_weight,
                'diamond_clarity': supplier_product.diamond_clarity,
                'supplier_user_id': supplier_product.supplier_id,
                'is_approved': True
            }
        )
        
        if not created:
            product.name = supplier_product.name
            product.description = supplier_product.description
            product.cost_price = supplier_product.cost_price
            # Do NOT update stock_quantity here; it's managed by Purchase Orders
            product.save()

        # Copy images if not already copied
        for img in supplier_product.images.all():
            if not ProductImage.objects.filter(product=product, image=img.image).exists():
                ProductImage.objects.create(
                    product=product,
                    image=img.image,
                    is_primary=img.is_primary
                )

        return Response({'status': 'approved', 'product_id': str(product.id)})

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
    filterset_fields = ['category__slug', 'purity', 'is_featured', 'is_approved']
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
        base_qs = PurchaseOrder.objects.all().select_related('supplier', 'product')
        if self.request.user.is_authenticated:
            if self.request.user.role == 'ADMIN':
                return base_qs
            elif self.request.user.role == 'SUPPLIER':
                return base_qs.filter(supplier=self.request.user)
        return PurchaseOrder.objects.none()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_received(self, request, pk=None):
        purchase_order = self.get_object()
        if purchase_order.status == 'RECEIVED':
            return Response({'error': 'Already received'}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            purchase_order.status = 'RECEIVED'
            purchase_order.save()
            
            from .services import StockService
            StockService.update_stock(
                product_id=purchase_order.product.id,
                quantity_change=purchase_order.quantity,
                entry_type='PURCHASE',
                reference_id=f"PO-{purchase_order.id}"
            )
            
            # Sync SupplierProduct stock
            if purchase_order.product.supplier_product:
                sp = purchase_order.product.supplier_product
                sp.stock_quantity = max(0, sp.stock_quantity - purchase_order.quantity)
                sp.save()

        return Response({'status': 'Purchase order marked as received'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def supplier_orders(self, request):
        orders = PurchaseOrder.objects.filter(supplier=request.user)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class CustomerOrderViewSet(viewsets.ModelViewSet):
    queryset = CustomerOrder.objects.all()
    serializer_class = CustomerOrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'product']
    ordering_fields = ['created_at', '-created_at']
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsCustomer()]
        elif self.action == 'my_orders':
            return [IsCustomer()]
        return [IsAdmin()]
    
    def get_queryset(self):
        base_qs = CustomerOrder.objects.all().select_related('customer', 'product')
        if self.request.user.is_authenticated:
            if self.request.user.role == 'ADMIN':
                return base_qs
            elif self.request.user.role == 'CUSTOMER':
                return base_qs.filter(customer=self.request.user)
        return CustomerOrder.objects.none()
    
    def perform_create(self, serializer):
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=serializer.validated_data['product'].id)
            quantity = serializer.validated_data['quantity']
            
            if not product.is_approved or not product.is_available_for_sale:
                raise ValidationError("Product is not available for sale")
            
            # Save first to get the instance ID for reference
            instance = serializer.save(customer=self.request.user)

            from .services import StockService
            StockService.update_stock(
                product_id=product.id,
                quantity_change=-quantity,
                entry_type='SALE',
                reference_id=f"CUST-ORD-{instance.id}"
            )
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        orders = CustomerOrder.objects.filter(customer=request.user)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        if order.customer != request.user and request.user.role != 'ADMIN':
            raise PermissionDenied("You can only cancel your own orders")
        
        if order.status == 'PLACED':
            with transaction.atomic():
                order.status = 'CANCELLED'
                order.save()

                from .services import StockService
                StockService.update_stock(
                    product_id=order.product.id,
                    quantity_change=order.quantity,
                    entry_type='CANCEL',
                    reference_id=f"CUST-ORD-{order.id}"
                )
            return Response({'status': 'Order cancelled'}, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Can only cancel PLACED orders'},
            status=status.HTTP_400_BAD_REQUEST
        )

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
