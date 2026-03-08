from django.db import transaction
from django.db.models import F
from .models import Product, StockLedger

class StockService:
    @staticmethod
    def update_stock(product_id, quantity_change, entry_type, reference_id):
        """
        Atomic stock update with ledger entry.
        quantity_change: positive for addition, negative for deduction.
        """
        with transaction.atomic():
            # Use select_for_update to lock the row (if supported by the DB backend)
            product = Product.objects.select_for_update().get(id=product_id)
            
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
