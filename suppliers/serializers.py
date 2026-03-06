from rest_framework import serializers
from .models import Supplier

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('id', 'user', 'company_name', 'gst_number', 'pan_number', 'business_address', 'is_verified', 'certificate', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
