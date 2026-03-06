from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from .models import Order, OrderItem, OrderStatusLog, OrderTracking, OrderTimelineEvent, OrderAction
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderSerializer, 
    UpdateOrderStatusSerializer, UpdateTrackingSerializer, 
    CreateOrderActionSerializer, ApproveOrderActionSerializer, OrderTrackingSerializer,
    OrderTimelineEventSerializer
)
from cart.models import Cart
from products.models import Product, StockLedger
from decimal import Decimal

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['order_number', 'tracking_number', 'user__email']
    ordering_fields = ['created_at', 'status', 'net_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if hasattr(user, 'role') and user.role == 'ADMIN':
                return Order.objects.all().prefetch_related('items', 'status_history', 'tracking', 'timeline_events', 'actions')
            return Order.objects.filter(user=user).prefetch_related('items', 'status_history', 'tracking', 'timeline_events', 'actions')
        return Order.objects.none()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        elif self.action == 'list':
            return OrderListSerializer
        elif self.action in ['update_status', 'update_tracking']:
            return UpdateOrderStatusSerializer
        elif self.action == 'create_action':
            return CreateOrderActionSerializer
        elif self.action == 'approve_action':
            return ApproveOrderActionSerializer
        return OrderSerializer

    @action(detail=False, methods=['get'], url_path='my-orders')
    def my_orders(self, request):
        orders = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            cart = Cart.objects.select_for_update().get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        order_items_data = []
        for cart_item in cart.items.select_related('product'):
            product = Product.objects.select_for_update().get(id=cart_item.product.id)
            
            if not product.is_available_for_sale:
                return Response(
                    {"detail": f"Product {product.name} is currently not available for sale."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if product.stock_quantity < cart_item.quantity:
                return Response(
                    {"detail": f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            order_items_data.append({
                'product': product,
                'quantity': cart_item.quantity,
                'price': product.retail_price,
                'cost_price': product.cost_price,
                'subtotal': cart_item.subtotal
            })

        total_amount = cart.total_price
        gst_amount = total_amount * Decimal('0.03')
        net_amount = total_amount + gst_amount

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(
            user=request.user,
            total_amount=total_amount,
            tax_amount=gst_amount,
            net_amount=net_amount,
            status='PENDING_PAYMENT'
        )

        for item_data in order_items_data:
            product = item_data['product']
            qty = item_data['quantity']
            prev_stock = product.stock_quantity
            
            OrderItem.objects.create(
                order=order,
                product=product,
                supplier=product.supplier,
                quantity=qty,
                price=item_data['price'],
                cost_price=item_data['cost_price'],
                gst_amount=item_data['price'] * Decimal('0.03') * qty,
                subtotal=item_data['subtotal']
            )
            
            product.stock_quantity -= qty
            
            # Auto-disable if stock hits zero
            if product.stock_quantity <= 0:
                product.is_available_for_sale = False
                
            product.save()

            # Record in Ledger
            StockLedger.objects.create(
                product=product,
                entry_type='SALE',
                quantity=-qty,
                reference_id=f"ORD-{order.order_number}",
                previous_stock=prev_stock,
                current_stock=product.stock_quantity
            )

        cart.items.all().delete()

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        
        if not request.user.is_authenticated or (request.user.role != 'ADMIN' and request.user != order.user):
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        old_status = order.status
        order.status = serializer.validated_data['status']
        
        if order.status == 'DELIVERED':
            order.actual_delivery_date = timezone.now().date()
        
        order.save(update_fields=['status', 'actual_delivery_date', 'updated_at'])
        
        OrderStatusLog.objects.create(
            order=order,
            previous_status=old_status,
            new_status=order.status,
            changed_by=request.user,
            notes=serializer.validated_data.get('notes', '')
        )
        
        OrderTimelineEvent.objects.create(
            order=order,
            event_type='STATUS_CHANGE',
            title=f'Order Status Updated',
            description=f'Status changed from {old_status} to {order.status}',
            user=request.user
        )
        
        return Response(OrderDetailSerializer(order).data)

    @action(detail=True, methods=['post'])
    def update_tracking(self, request, pk=None):
        order = self.get_object()
        
        if not request.user.is_authenticated or request.user.role != 'ADMIN':
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            tracking = order.tracking
        except OrderTracking.DoesNotExist:
            return Response({"detail": "Tracking not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UpdateTrackingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        for field, value in serializer.validated_data.items():
            setattr(tracking, field, value)
        tracking.save()
        
        if serializer.validated_data.get('current_location'):
            OrderTimelineEvent.objects.create(
                order=order,
                event_type='LOCATION_UPDATE',
                title='Location Updated',
                description=f'Package is now at {serializer.validated_data["current_location"]}',
                location=serializer.validated_data['current_location'],
                user=request.user
            )
        
        return Response(OrderTrackingSerializer(tracking).data)

    @action(detail=True, methods=['post'])
    def create_action(self, request, pk=None):
        order = self.get_object()
        
        serializer = CreateOrderActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_obj = OrderAction.objects.create(
            order=order,
            action_type=serializer.validated_data['action_type'],
            description=serializer.validated_data.get('description', ''),
            requested_by=request.user
        )
        
        OrderTimelineEvent.objects.create(
            order=order,
            event_type='CUSTOMER_NOTE' if request.user == order.user else 'ADMIN_NOTE',
            title=f'Action Requested: {action_obj.get_action_type_display()}',
            description=serializer.validated_data.get('description', ''),
            user=request.user
        )
        
        return Response({
            'id': action_obj.id,
            'action_type': action_obj.action_type,
            'status': action_obj.status,
            'message': 'Action request submitted successfully'
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve_action(self, request, pk=None):
        order = self.get_object()
        
        if not request.user.is_authenticated or request.user.role != 'ADMIN':
            return Response({"detail": "Only admins can approve actions"}, status=status.HTTP_403_FORBIDDEN)
        
        action_id = request.data.get('action_id')
        try:
            action_obj = OrderAction.objects.get(id=action_id, order=order)
        except OrderAction.DoesNotExist:
            return Response({"detail": "Action not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ApproveOrderActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if serializer.validated_data['action'] == 'approve':
            action_obj.status = 'APPROVED'
            action_obj.approved_by = request.user
            action_obj.completed_at = timezone.now()
            action_obj.save()
        else:
            action_obj.status = 'REJECTED'
            action_obj.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            action_obj.save()
        
        return Response({'status': action_obj.status, 'message': 'Action updated'})

    @action(detail=False, methods=['get'])
    def timeline(self, request):
        order_id = request.query_params.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_authenticated or (request.user.role != 'ADMIN' and request.user != order.user):
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        events = order.timeline_events.all()
        serializer = OrderTimelineEventSerializer(events, many=True)
        return Response(serializer.data)
