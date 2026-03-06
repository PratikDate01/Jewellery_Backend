from django.db import models
from django.conf import settings

class Supplier(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=15, unique=True)
    pan_number = models.CharField(max_length=10, unique=True)
    business_address = models.TextField()
    is_verified = models.BooleanField(default=False)
    certificate = models.FileField(upload_to='suppliers/certificates/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name
