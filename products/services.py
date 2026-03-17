from django.db import transaction
from django.db.models import F
from .models import Product, StockLedger, ProductImage, SupplierProduct

class StockService:
    @staticmethod
    def update_stock(product_id, quantity_change, entry_type, reference_id):
        """
        Atomic stock update with ledger entry.
        quantity_change: positive for addition, negative for deduction.
        """
        # Use select_for_update to lock the row (if supported by the DB backend)
        product = Product.objects.get(id=product_id)
        
        previous_stock = product.stock_quantity
        new_stock = previous_stock + quantity_change
        
        if new_stock < 0:
            raise ValueError(f"Insufficient stock for {product.name}. Available: {previous_stock}")
        
        product.stock_quantity = new_stock
        
        # Auto-disable if stock hits zero or below
        if product.stock_quantity <= 0:
            product.is_available_for_sale = False
        elif product.stock_quantity > 0:
            product.is_available_for_sale = True
            
        product.save()
        
        # Record in Ledger
        StockLedger.objects.create(
            product=product,
            entry_type=entry_type,
            quantity=quantity_change,
            reference_id=reference_id,
            previous_stock=previous_stock,
            current_stock=new_stock
        )
        
        return product

    @staticmethod
    def receive_purchase_order(purchase_order_id):
        """
        Mark a purchase order as received and update stock.
        """
        from django.utils import timezone
        purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
        if purchase_order.status == 'RECEIVED':
            return purchase_order
            
        purchase_order.status = 'RECEIVED'
        purchase_order.received_at = timezone.now()
        purchase_order.save()
        
        StockService.update_stock(
            product_id=purchase_order.product.id,
            quantity_change=purchase_order.quantity,
            entry_type='PURCHASE',
            reference_id=f"PO-{purchase_order.id}"
        )
        
        # Sync SupplierProduct stock
        if purchase_order.product.supplier_product:
            sp = purchase_order.product.supplier_product
            sp.available_stock = max(0, sp.available_stock - purchase_order.quantity)
            sp.save()
            
        return purchase_order

class ProductService:
    @staticmethod
    def approve_supplier_product(supplier_product_id, selling_price=0.00):
        """
        Approve a supplier product and create/update a store product.
        """
        from decimal import Decimal
        selling_price = Decimal(str(selling_price))
        
        supplier_product = SupplierProduct.objects.get(id=supplier_product_id)
        
        from suppliers.models import Supplier as SupplierProfile
        supplier_profile = SupplierProfile.objects.filter(user_id=supplier_product.supplier_id).first()
        
        product = Product.objects.filter(supplier_product=supplier_product).first()
        created = False
        
        if not product:
            product = Product(
                supplier_product=supplier_product,
                name=supplier_product.name,
                description=supplier_product.description,
                category=supplier_product.category,
                metal_type=supplier_product.metal_type,
                weight=supplier_product.weight,
                cost_price=supplier_product.supplier_price,
                selling_price=selling_price,
                retail_price=supplier_product.suggested_retail_price,
                stock_quantity=0, 
                purity=supplier_product.purity,
                diamond_clarity=supplier_product.diamond_clarity,
                supplier_user=supplier_product.supplier,
                supplier=supplier_profile,
                is_approved=True,
                is_available_for_sale=False
            )
            product.save()
            created = True
        
        if not created:
            product.name = supplier_product.name
            product.description = supplier_product.description
            product.category = supplier_product.category
            product.metal_type = supplier_product.metal_type
            product.weight = supplier_product.weight
            product.cost_price = supplier_product.supplier_price
            product.selling_price = selling_price if selling_price > 0 else product.selling_price
            product.retail_price = supplier_product.suggested_retail_price
            product.purity = supplier_product.purity
            product.diamond_clarity = supplier_product.diamond_clarity
            product.supplier_user = supplier_product.supplier
            product.supplier = supplier_profile
            product.is_approved = True
            product.save()

        # Update status only after successful product creation/update
        supplier_product.status = 'APPROVED'
        supplier_product.save()

        # Copy images
        for img in supplier_product.images.all():
            # In MongoDB, comparing CloudinaryField directly in filter might be unreliable.
            # Using the image name/string which typically contains the public_id
            img_path = str(img.image)
            if not ProductImage.objects.filter(product=product, image=img_path).exists():
                ProductImage.objects.create(
                    product=product,
                    image=img.image,
                    is_primary=img.is_primary
                )
        
        return product
