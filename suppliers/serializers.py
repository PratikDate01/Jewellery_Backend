from rest_framework import serializers
from .models import Supplier
from accounts.fields import ObjectIdField

class SupplierSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    class Meta:
        model = Supplier
        fields = ('id', 'user', 'company_name', 'gst_number', 'pan_number', 'business_address', 'is_verified', 'certificate', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
