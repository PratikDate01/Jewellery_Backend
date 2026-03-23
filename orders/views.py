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
from products.services import StockService
from decimal import Decimal

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
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
                'price': product.selling_price,
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
            
            # Use StockService for atomic update and ledger entry
            StockService.update_stock(
                product_id=product.id,
                quantity_change=-qty,
                entry_type='SALE',
                reference_id=f"ORD-{order.order_number}"
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
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        # Check if user is owner
        if order.user != request.user and request.user.role != 'ADMIN':
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            
        # Check if order can be cancelled
        if order.status in ['SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED', 'RETURNED']:
            return Response({"detail": f"Order cannot be cancelled in status: {order.status}"}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            old_status = order.status
            order.status = 'CANCELLED'
            
            # Professional Refund System logic
            if order.payment_status == 'PAID':
                order.payment_status = 'REFUND_PENDING'
                order.status = 'REFUND_INITIATED'
                
                # Update Payment record if it exists
                if hasattr(order, 'payment'):
                    payment = order.payment
                    payment.status = 'REFUNDED' # Or REFUND_PENDING if real-world integration
                    payment.save()
            
            order.save()
            
            # Restock items
            for item in order.items.all():
                if item.product:
                    StockService.update_stock(
                        product_id=item.product.id,
                        quantity_change=item.quantity,
                        entry_type='RETURN',
                        reference_id=f"CANCEL-{order.order_number}"
                    )
            
            # Log status change
            OrderStatusLog.objects.create(
                order=order,
                previous_status=old_status,
                new_status=order.status,
                changed_by=request.user,
                notes=request.data.get('reason', 'Customer cancelled the order')
            )
            
            # Timeline event
            OrderTimelineEvent.objects.create(
                order=order,
                event_type='STATUS_CHANGE',
                title='Order Cancelled',
                description=f'Order was cancelled by {request.user.email}. Reason: {request.data.get("reason", "N/A")}',
                user=request.user
            )
            
            if order.payment_status == 'REFUND_PENDING':
                OrderTimelineEvent.objects.create(
                    order=order,
                    event_type='REFUND_INITIATED',
                    title='Refund Initiated',
                    description=f'Refund of {order.net_amount} has been initiated.',
                    user=request.user
                )

        return Response(OrderDetailSerializer(order).data)

    @action(detail=True, methods=['delete'])
    def delete_order(self, request, pk=None):
        if not request.user.is_authenticated or request.user.role != 'ADMIN':
            return Response({"detail": "Only admins can delete orders"}, status=status.HTTP_403_FORBIDDEN)
            
        order = self.get_object()
        order_num = order.order_number
        order.delete()
        
        return Response({"detail": f"Order {order_num} has been deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

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
            with transaction.atomic():
                action_obj.status = 'APPROVED'
                action_obj.approved_by = request.user
                action_obj.completed_at = timezone.now()
                action_obj.save()
                
                # Perform the actual action logic
                if action_obj.action_type == 'CANCEL_ORDER':
                    # Call the cancel logic (reusing same logic)
                    old_status = order.status
                    order.status = 'CANCELLED'
                    
                    if order.payment_status == 'PAID':
                        order.payment_status = 'REFUND_PENDING'
                        order.status = 'REFUND_INITIATED'
                        if hasattr(order, 'payment'):
                            payment = order.payment
                            payment.status = 'REFUNDED'
                            payment.save()
                    
                    order.save()
                    
                    # Restock
                    for item in order.items.all():
                        if item.product:
                            StockService.update_stock(
                                product_id=item.product.id,
                                quantity_change=item.quantity,
                                entry_type='RETURN',
                                reference_id=f"CANCEL-ACTION-{order.order_number}"
                            )
                    
                    OrderTimelineEvent.objects.create(
                        order=order,
                        event_type='STATUS_CHANGE',
                        title='Order Cancelled (Approved)',
                        description=f'Cancellation request approved by {request.user.email}',
                        user=request.user
                    )
                
                elif action_obj.action_type == 'REFUND_REQUEST':
                    order.payment_status = 'REFUND_PENDING'
                    order.status = 'REFUND_INITIATED'
                    order.save()
                    
                    if hasattr(order, 'payment'):
                        payment = order.payment
                        payment.status = 'REFUNDED'
                        payment.save()
                        
                    OrderTimelineEvent.objects.create(
                        order=order,
                        event_type='REFUND_INITIATED',
                        title='Refund Approved',
                        description=f'Refund request approved by {request.user.email}',
                        user=request.user
                    )
        else:
            action_obj.status = 'REJECTED'
            action_obj.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            action_obj.save()
            
            OrderTimelineEvent.objects.create(
                order=order,
                event_type='ADMIN_NOTE',
                title=f'Action Rejected: {action_obj.get_action_type_display()}',
                description=f'Reason: {action_obj.rejection_reason}',
                user=request.user
            )
        
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
