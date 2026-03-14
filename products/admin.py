from django.contrib import admin
from .models import Product, ProductImage, PurchaseOrder, SupplierPayment, SupplierProduct, StockLedger

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

@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'category', 'status', 'metal_type', 'weight', 'supplier_price', 'available_stock', 'created_at']
    list_filter = ['status', 'category', 'metal_type', 'purity']
    search_fields = ['name', 'supplier__email', 'supplier_sku']
    inlines = [ProductImageInline]
    actions = ['approve_products', 'reject_products']

    def approve_products(self, request, queryset):
        for sp in queryset:
            if sp.status != 'APPROVED':
                # For admin bulk action, we might need a default selling price or just skip
                # Usually admin would approve one by one to set price, but here we can set a default
                from .services import ProductService
                ProductService.approve_supplier_product(sp.id, sp.suggested_retail_price)
    approve_products.short_description = "Approve selected products (using suggested retail price)"

    def reject_products(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_products.short_description = "Reject selected products"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'supplier_user', 'category', 'metal_type', 'weight', 'cost_price', 'selling_price', 'stock_quantity', 'is_approved', 'is_available_for_sale']
    list_filter = ['is_approved', 'is_available_for_sale', 'category', 'metal_type', 'purity']
    search_fields = ['name', 'sku', 'supplier_user__email']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ['sku', 'margin', 'margin_percentage', 'stock_quantity']
    actions = ['set_available_for_sale']

    def set_available_for_sale(self, request, queryset):
        queryset.update(is_available_for_sale=True)
    set_available_for_sale.short_description = "Mark selected as available for sale"

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'supplier', 'product', 'quantity', 'unit_cost_price', 'total_cost', 'status', 'payment_status_display', 'created_at']
    list_filter = ['status', 'supplier', 'created_at']
    search_fields = ['id', 'supplier__email', 'product__name']
    readonly_fields = ['total_cost', 'created_at', 'updated_at', 'amount_paid_display', 'remaining_amount_display', 'payment_status_display']
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
        from .services import StockService
        for po in queryset:
            if po.status != 'RECEIVED':
                StockService.receive_purchase_order(po.id)
    mark_received.short_description = "Mark selected purchase orders as received"

@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ['product', 'entry_type', 'quantity', 'previous_stock', 'current_stock', 'reference_id', 'created_at']
    list_filter = ['entry_type', 'created_at']
    search_fields = ['product__name', 'reference_id']
    readonly_fields = ['created_at']
