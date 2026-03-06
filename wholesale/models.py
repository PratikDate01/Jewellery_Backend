from django.db import models
from django.conf import settings
from products.models import Product

class WholesaleProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wholesale_profile')
    company_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=15, unique=True)
    pan_number = models.CharField(max_length=10, unique=True)
    business_address = models.TextField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

class NegotiationRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )

    wholesaler = models.ForeignKey(WholesaleProfile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    offered_price = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_response = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Negotiation by {self.wholesaler.company_name} for {self.product.name}"
