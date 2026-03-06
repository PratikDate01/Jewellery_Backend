from django.contrib import admin
from .models import Order, OrderItem, OrderStatusLog, OrderTracking, OrderTimelineEvent, OrderAction

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')

class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ('previous_status', 'new_status', 'changed_by', 'created_at')
    can_delete = False

class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0
    readonly_fields = ('tracking_number', 'created_at', 'last_updated')

class OrderActionInline(admin.TabularInline):
    model = OrderAction
    extra = 0
    readonly_fields = ('requested_at', 'updated_at', 'completed_at')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_status', 'net_amount', 'estimated_delivery_date', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at', 'carrier_name']
    search_fields = ['order_number', 'tracking_number', 'user__email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'user', 'status', 'payment_status', 'payment_method')}),
        ('Tracking', {'fields': ('tracking_number', 'current_location', 'carrier_name')}),
        ('Pricing', {'fields': ('total_amount', 'tax_amount', 'discount_amount', 'net_amount')}),
        ('Shipping Address', {'fields': ('full_name', 'phone', 'address_line_1', 'address_line_2', 'city', 'state', 'pincode')}),
        ('Delivery', {'fields': ('estimated_delivery_date', 'actual_delivery_date')}),
        ('Notes', {'fields': ('notes',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    inlines = [OrderItemInline, OrderStatusLogInline, OrderTrackingInline, OrderActionInline]
    actions = ['mark_paid', 'mark_processing', 'mark_packed', 'mark_shipped', 'mark_delivered']
    
    def mark_paid(self, request, queryset):
        queryset.update(payment_status='PAID', status='ORDER_CONFIRMED')
    mark_paid.short_description = "Mark selected orders as PAID"
    
    def mark_processing(self, request, queryset):
        queryset.update(status='PROCESSING')
    mark_processing.short_description = "Mark selected orders as PROCESSING"
    
    def mark_packed(self, request, queryset):
        queryset.update(status='PACKED')
    mark_packed.short_description = "Mark selected orders as PACKED"
    
    def mark_shipped(self, request, queryset):
        queryset.update(status='SHIPPED')
    mark_shipped.short_description = "Mark selected orders as SHIPPED"
    
    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='DELIVERED', actual_delivery_date=timezone.now().date())
    mark_delivered.short_description = "Mark selected orders as DELIVERED"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'subtotal']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['order', 'product', 'quantity', 'price', 'gst_amount', 'subtotal']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ['order', 'previous_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['order__order_number']
    readonly_fields = ['order', 'previous_status', 'new_status', 'changed_by', 'notes', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'order', 'status', 'current_location', 'estimated_delivery', 'actual_delivery_date']
    list_filter = ['status', 'carrier', 'created_at']
    search_fields = ['tracking_number', 'order__order_number']
    readonly_fields = ['tracking_number', 'order', 'created_at', 'last_updated']
    ordering = ['-created_at']

@admin.register(OrderTimelineEvent)
class OrderTimelineEventAdmin(admin.ModelAdmin):
    list_display = ['order', 'event_type', 'title', 'user', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['order__order_number', 'title', 'description']
    readonly_fields = ['order', 'event_type', 'title', 'description', 'user', 'location', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(OrderAction)
class OrderActionAdmin(admin.ModelAdmin):
    list_display = ['order', 'action_type', 'status', 'requested_by', 'requested_at']
    list_filter = ['status', 'action_type', 'requested_at']
    search_fields = ['order__order_number', 'description']
    readonly_fields = ['requested_at', 'updated_at']
    actions = ['approve_actions', 'reject_actions']
    
    fieldsets = (
        ('Action Info', {'fields': ('order', 'action_type', 'status', 'description')}),
        ('Approval', {'fields': ('requested_by', 'approved_by', 'rejection_reason')}),
        ('Timestamps', {'fields': ('requested_at', 'updated_at', 'completed_at')}),
    )
    
    def approve_actions(self, request, queryset):
        queryset.filter(status='PENDING').update(status='APPROVED', approved_by=request.user)
    approve_actions.short_description = "Approve selected actions"
    
    def reject_actions(self, request, queryset):
        queryset.filter(status='PENDING').update(status='REJECTED')
    reject_actions.short_description = "Reject selected actions"
