from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusLog, OrderTracking, OrderTimelineEvent, OrderAction
from products.serializers import ProductSerializer
from accounts.fields import ObjectIdField

class OrderItemSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'product_details', 'supplier', 'quantity', 'price', 'gst_amount', 'subtotal', 'status')

class OrderStatusLogSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True)
    previous_status_display = serializers.CharField(source='get_previous_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = ('id', 'previous_status', 'previous_status_display', 'new_status', 'new_status_display', 'changed_by_email', 'notes', 'created_at')
        read_only_fields = ('id', 'previous_status', 'previous_status_display', 'new_status', 'new_status_display', 'changed_by_email', 'notes', 'created_at')

class OrderTrackingSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderTracking
        fields = ('id', 'tracking_number', 'carrier', 'carrier_url', 'status', 'status_display', 'current_location', 'picked_up_date', 'estimated_delivery', 'actual_delivery_date', 'last_updated', 'created_at')
        read_only_fields = ('tracking_number', 'created_at', 'last_updated')

class OrderTimelineEventSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = OrderTimelineEvent
        fields = ('id', 'event_type', 'event_type_display', 'title', 'description', 'user_email', 'location', 'created_at')
        read_only_fields = ('id', 'event_type', 'event_type_display', 'title', 'description', 'user_email', 'location', 'created_at')

class OrderActionSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    requested_by_email = serializers.EmailField(source='requested_by.email', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderAction
        fields = ('id', 'action_type', 'action_type_display', 'status', 'status_display', 'requested_by_email', 'approved_by_email', 'description', 'rejection_reason', 'requested_at', 'updated_at', 'completed_at')
        read_only_fields = ('requested_at', 'updated_at', 'completed_at')

class OrderSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'order_number', 'user_email', 'status', 'payment_status', 'total_amount', 'tax_amount', 'net_amount', 'items', 'created_at')
        read_only_fields = ('id', 'order_number', 'user_email', 'status', 'payment_status', 'total_amount', 'tax_amount', 'net_amount', 'items', 'created_at')

class OrderDetailSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusLogSerializer(many=True, read_only=True)
    tracking = OrderTrackingSerializer(read_only=True)
    timeline_events = OrderTimelineEventSerializer(many=True, read_only=True)
    actions = OrderActionSerializer(many=True, read_only=True)
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'tracking_number', 'user_email', 'status', 'status_display',
            'payment_status', 'payment_status_display', 'payment_method',
            'total_amount', 'tax_amount', 'discount_amount', 'net_amount',
            'full_name', 'phone', 'address_line_1', 'address_line_2', 'city', 'state', 'pincode',
            'estimated_delivery_date', 'actual_delivery_date', 'current_location', 'carrier_name',
            'notes', 'items', 'status_history', 'tracking', 'timeline_events', 'actions',
            'created_at', 'updated_at'
        )
        read_only_fields = ('order_number', 'tracking_number', 'status', 'payment_status', 'created_at', 'updated_at')

class OrderListSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    tracking_number = serializers.CharField(source='tracking.tracking_number', read_only=True, allow_null=True)
    item_count = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'tracking_number', 'user_email', 'status', 'status_display', 
            'payment_status', 'payment_status_display', 'total_amount', 'tax_amount', 
            'net_amount', 'item_count', 'items', 'estimated_delivery_date', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'order_number', 'tracking_number', 'user_email', 'status', 'status_display', 'payment_status', 'payment_status_display', 'net_amount', 'item_count', 'created_at', 'updated_at')
    
    def get_item_count(self, obj):
        return obj.items.count()

class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)

class UpdateTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderTracking
        fields = ('status', 'current_location', 'carrier', 'carrier_url', 'estimated_delivery', 'picked_up_date')

class CreateOrderActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderAction
        fields = ('action_type', 'description')

class ApproveOrderActionSerializer(serializers.Serializer):
    APPROVE_CHOICES = [('approve', 'Approve'), ('reject', 'Reject')]
    action = serializers.ChoiceField(choices=APPROVE_CHOICES)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
