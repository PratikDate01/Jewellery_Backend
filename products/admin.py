from django.contrib import admin
from .models import Product, ProductImage, PurchaseOrder, SupplierPayment

class SupplierPaymentInline(admin.TabularInline):
    model = SupplierPayment
    extra = 1

@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'purchase_order', 'amount_paid', 'payment_method', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['purchase_order__id', 'transaction_id']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier_user', 'category', 'cost_price', 'selling_price', 'stock_quantity', 'is_approved', 'is_featured']
    list_filter = ['is_approved', 'is_featured', 'category', 'supplier_user', 'purity']
    search_fields = ['name', 'sku', 'supplier_user__email']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ['sku', 'margin', 'margin_percentage']
    actions = ['approve_products']

    def approve_products(self, request, queryset):
        queryset.update(is_approved=True)
    approve_products.short_description = "Approve selected products"

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['product__name']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'product', 'quantity', 'total_cost', 'amount_paid_display', 'remaining_amount_display', 'payment_status_display', 'status', 'created_at']
    list_filter = ['status', 'supplier', 'created_at']
    search_fields = ['id', 'supplier__email', 'product__name']
    readonly_fields = ['created_at', 'updated_at', 'amount_paid_display', 'remaining_amount_display', 'payment_status_display']
    inlines = [SupplierPaymentInline]
    actions = ['mark_received']
    
    def amount_paid_display(self, obj):
        return f"₹{obj.amount_paid:.2f}"
    amount_paid_display.short_description = 'Amount Paid'
    
    def remaining_amount_display(self, obj):
        return f"₹{obj.remaining_amount:.2f}"
    remaining_amount_display.short_description = 'Remaining'
    
    def payment_status_display(self, obj):
        return obj.payment_status
    payment_status_display.short_description = 'Payment Status'
    
    def mark_received(self, request, queryset):
        queryset.update(status='RECEIVED')
    mark_received.short_description = "Mark selected purchase orders as received"
