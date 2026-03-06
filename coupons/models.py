from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('PERCENTAGE', 'Percentage'),
        ('FLAT', 'Flat Amount'),
    )

    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='PERCENTAGE')
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    min_cart_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    
    usage_limit = models.PositiveIntegerField(default=0)
    used_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        if not self.active:
            return False
        
        now = timezone.now()
        
        if self.valid_from and self.valid_from > now:
            return False
        
        if self.valid_to and self.valid_to < now:
            return False
        
        if self.usage_limit > 0 and self.used_count >= self.usage_limit:
            return False
        
        return True

    @property
    def discount_percentage(self):
        if self.discount_type == 'PERCENTAGE':
            return float(self.value)
        return None

    @property
    def discount_amount(self):
        if self.discount_type == 'FLAT':
            return float(self.value)
        return None
