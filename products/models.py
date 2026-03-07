from django.db import models, transaction
from django.utils.text import slugify
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from categories.models import Category
from suppliers.models import Supplier
from cloudinary.models import CloudinaryField
import cloudinary.uploader

class SupplierProduct(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    supplier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplier_products', limit_choices_to={'role': 'SUPPLIER'})
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='supplier_products')
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    gold_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, default=0.00)
    purity = models.CharField(max_length=10, choices=(
        ('18K', '18 Karat'),
        ('22K', '22 Karat'),
        ('24K', '24 Karat'),
    ), default='22K')
    
    diamond_clarity = models.CharField(max_length=10, choices=(
        ('IF', 'Internally Flawless'),
        ('VVS1', 'Very Very Slightly Included 1'),
        ('VVS2', 'Very Very Slightly Included 2'),
        ('VS1', 'Very Slightly Included 1'),
        ('VS2', 'Very Slightly Included 2'),
        ('SI1', 'Slightly Included 1'),
        ('SI2', 'Slightly Included 2'),
        ('I1', 'Included 1'),
    ), null=True, blank=True)
    
    stock_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    admin_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.supplier.email})"

class Product(models.Model):
    PURITY_CHOICES = (
        ('18K', '18 Karat'),
        ('22K', '22 Karat'),
        ('24K', '24 Karat'),
    )

    CLARITY_CHOICES = (
        ('IF', 'Internally Flawless'),
        ('VVS1', 'Very Very Slightly Included 1'),
        ('VVS2', 'Very Very Slightly Included 2'),
        ('VS1', 'Very Slightly Included 1'),
        ('VS2', 'Very Slightly Included 2'),
        ('SI1', 'Slightly Included 1'),
        ('SI2', 'Slightly Included 2'),
        ('I1', 'Included 1'),
    )

    supplier_product = models.OneToOneField(SupplierProduct, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_store_product')
    supplier_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplied_products', null=True, blank=True, limit_choices_to={'role': 'SUPPLIER'})
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Snapshot of the price admin pays to supplier")
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Price customer pays")
    
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0.00)
    making_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    
    gold_weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, default=0.00)
    purity = models.CharField(max_length=10, choices=PURITY_CHOICES, default='22K')
    diamond_clarity = models.CharField(max_length=10, choices=CLARITY_CHOICES, null=True, blank=True)
    
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=2)
    sku = models.CharField(max_length=50, unique=True, editable=False)
    
    is_featured = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    is_available_for_sale = models.BooleanField(default=False, help_text="Strict: True only if stock is received by Admin")
    
    hallmark_certificate = models.FileField(upload_to='hallmarks/', null=True, blank=True)
    video = models.FileField(upload_to='product_videos/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_enabled', 'is_approved', 'is_available_for_sale']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            original_slug = slugify(self.name)
            unique_slug = original_slug
            num = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{original_slug}-{num}'
                num += 1
            self.slug = unique_slug
        
        if not self.sku:
            # For MongoDB, we shouldn't increment based on ObjectId. 
            # Use count or timestamp-based generation instead.
            count = Product.objects.count() + 1
            import time
            timestamp = int(time.time()) % 10000
            self.sku = f"PROD-{timestamp:04d}-{count:03d}"
            
        super().save(*args, **kwargs)
    
    @property
    def margin(self):
        if self.cost_price > 0:
            return self.selling_price - self.cost_price
        return 0
    
    @property
    def margin_percentage(self):
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    supplier_product = models.ForeignKey(SupplierProduct, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = CloudinaryField('image', folder='products/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    )
    
    supplier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchase_orders', limit_choices_to={'role': 'SUPPLIER'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchase_orders')
    quantity = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def amount_paid(self):
        return self.payments.aggregate(total=models.Sum('amount_paid'))['total'] or 0

    @property
    def remaining_amount(self):
        return self.total_cost - self.amount_paid

    @property
    def payment_status(self):
        paid = self.amount_paid
        if paid <= 0:
            return 'PENDING'
        if paid < self.total_cost:
            return 'PARTIAL'
        return 'PAID'

    def __str__(self):
        return f"PO #{self.id} - {self.product.name} x {self.quantity}"


class SupplierPayment(models.Model):
    METHOD_CHOICES = (
        ('UPI', 'UPI'),
        ('BANK', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('CREDIT', 'Credit'),
    )

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of {self.amount_paid} for PO #{self.purchase_order.id}"


class CustomerOrder(models.Model):
    STATUS_CHOICES = (
        ('PLACED', 'Placed'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    )
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_orders', limit_choices_to={'role': 'CUSTOMER'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='customer_orders')
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.email} - {self.product.name}"


@receiver(post_delete, sender=ProductImage)
def delete_cloudinary_image(sender, instance, **kwargs):
    if instance.image:
        try:
            public_id = instance.image.public_id
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {e}")


@receiver(post_save, sender=PurchaseOrder)
def handle_purchase_order_received(sender, instance, created, **kwargs):
    if not created and instance.status == 'RECEIVED':
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=instance.product.id)
            prev_stock = product.stock_quantity
            product.stock_quantity += instance.quantity
            
            # Auto-enable for sale once stock is physically received
            if product.stock_quantity > 0:
                product.is_available_for_sale = True
                
            product.save()

            # Sync SupplierProduct stock
            if product.supplier_product:
                sp = product.supplier_product
                sp.stock_quantity = max(0, sp.stock_quantity - instance.quantity)
                sp.save()

            # Record in Ledger
            StockLedger.objects.create(
                product=product,
                entry_type='PURCHASE',
                quantity=instance.quantity,
                reference_id=f"PO-{instance.id}",
                previous_stock=prev_stock,
                current_stock=product.stock_quantity
            )


class StockLedger(models.Model):
    ENTRY_TYPES = (
        ('PURCHASE', 'Inventory Purchase'),
        ('SALE', 'Retail Sale'),
        ('ADJUSTMENT', 'Stock Adjustment'),
        ('RETURN', 'Customer Return'),
        ('CANCEL', 'Order Cancellation'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_ledger')
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    quantity = models.IntegerField(help_text="Positive for additions, negative for deductions")
    reference_id = models.CharField(max_length=100, help_text="PO ID, Order ID, or Adjustment Reason")
    previous_stock = models.IntegerField()
    current_stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entry_type} | {self.product.name} | {self.quantity}"

    class Meta:
        ordering = ['-created_at']
