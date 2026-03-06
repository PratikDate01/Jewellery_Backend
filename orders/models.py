from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from products.models import Product
from suppliers.models import Supplier
import uuid

class Order(models.Model):
    STATUS_CHOICES = (
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('PAYMENT_CONFIRMED', 'Payment Confirmed'),
        ('ORDER_CONFIRMED', 'Order Confirmed'),
        ('PROCESSING', 'Processing'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUND_INITIATED', 'Refund Initiated'),
        ('REFUNDED', 'Refunded'),
        ('RETURNED', 'Returned'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUND_PENDING', 'Refund Pending'),
        ('REFUNDED', 'Refunded'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    
    order_number = models.CharField(max_length=50, unique=True, editable=False, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Shipping Address
    full_name = models.CharField(max_length=255, default="")
    phone = models.CharField(max_length=15, default="")
    address_line_1 = models.CharField(max_length=255, default="")
    address_line_2 = models.CharField(max_length=255, blank=True, null=True, default="")
    city = models.CharField(max_length=100, default="")
    state = models.CharField(max_length=100, default="")
    pincode = models.CharField(max_length=10, default="")
    
    # Order Details
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, default='CARD')
    
    estimated_delivery_date = models.DateField(blank=True, null=True)
    actual_delivery_date = models.DateField(blank=True, null=True)
    
    # Tracking
    current_location = models.CharField(max_length=255, blank=True, null=True)
    carrier_name = models.CharField(max_length=100, blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} by {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='order_items', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Price at the time of order
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Cost at the time of order
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # For split orders / supplier tracking
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, default='PENDING')

class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=30, blank=True, null=True)
    new_status = models.CharField(max_length=30, choices=Order.STATUS_CHOICES, default='PENDING_PAYMENT')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order.order_number}: {self.previous_status} → {self.new_status}"


class OrderTracking(models.Model):
    TRACKING_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PICKED_UP', 'Picked Up'),
        ('IN_TRANSIT', 'In Transit'),
        ('OUT_FOR_DELIVERY', 'Out For Delivery'),
        ('DELIVERED', 'Delivered'),
        ('FAILED_DELIVERY', 'Failed Delivery'),
        ('RETURNED', 'Returned'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='tracking')
    tracking_number = models.CharField(max_length=100, unique=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    carrier_url = models.URLField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=TRACKING_STATUS_CHOICES, default='PENDING')
    current_location = models.CharField(max_length=255, blank=True, null=True)
    
    picked_up_date = models.DateTimeField(blank=True, null=True)
    estimated_delivery = models.DateTimeField(blank=True, null=True)
    actual_delivery_date = models.DateTimeField(blank=True, null=True)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Tracking {self.tracking_number} - {self.status}"


class OrderTimelineEvent(models.Model):
    EVENT_TYPES = (
        ('STATUS_CHANGE', 'Status Changed'),
        ('PAYMENT_UPDATE', 'Payment Update'),
        ('LOCATION_UPDATE', 'Location Update'),
        ('DELIVERY_ATTEMPT', 'Delivery Attempt'),
        ('CUSTOMER_NOTE', 'Customer Note'),
        ('ADMIN_NOTE', 'Admin Note'),
        ('RETURN_REQUEST', 'Return Request'),
        ('REFUND_INITIATED', 'Refund Initiated'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='timeline_events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    location = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.event_type}: {self.title}"


class OrderAction(models.Model):
    ACTION_TYPES = (
        ('CONFIRM_ORDER', 'Confirm Order'),
        ('CANCEL_ORDER', 'Cancel Order'),
        ('RETURN_REQUEST', 'Request Return'),
        ('REFUND_REQUEST', 'Request Refund'),
        ('EDIT_SHIPPING', 'Edit Shipping Address'),
        ('UPDATE_TRACKING', 'Update Tracking'),
        ('ADD_NOTE', 'Add Note'),
    )
    
    ACTION_STATUS = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    status = models.CharField(max_length=20, choices=ACTION_STATUS, default='PENDING')
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='requested_actions')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_actions')
    
    description = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Action {self.id} - {self.action_type} ({self.status})"


@receiver(post_save, sender=Order)
def create_order_tracking(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'tracking'):
            tracking_number = f"TRK-{instance.order_number}-{uuid.uuid4().hex[:6].upper()}"
            OrderTracking.objects.create(
                order=instance,
                tracking_number=tracking_number
            )
            OrderTimelineEvent.objects.create(
                order=instance,
                event_type='STATUS_CHANGE',
                title='Order Created',
                description=f'Order {instance.order_number} created successfully'
            )


@receiver(post_save, sender=Order)
def log_order_status_change(sender, instance, **kwargs):
    update_fields = kwargs.get('update_fields')
    if update_fields and 'status' in update_fields:
        previous_status = Order.objects.filter(pk=instance.pk).values('status').first()
        if previous_status:
            OrderStatusLog.objects.create(
                order=instance,
                previous_status=previous_status['status'],
                new_status=instance.status
            )
            OrderTimelineEvent.objects.create(
                order=instance,
                event_type='STATUS_CHANGE',
                title=f'Order Status Updated',
                description=f'Status changed to {instance.get_status_display()}'
            )
