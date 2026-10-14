from django.db import models
from django.conf import settings

class Supplier(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=15, unique=True, null=True, blank=True, default=None)
    pan_number = models.CharField(max_length=10, unique=True, null=True, blank=True, default=None)
    business_address = models.TextField(blank=True, default='')
    is_verified = models.BooleanField(default=False)
    certificate = models.FileField(upload_to='suppliers/certificates/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.gst_number:
            self.gst_number = None
        if not self.pan_number:
            self.pan_number = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name
