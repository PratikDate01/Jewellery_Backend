from rest_framework import serializers
from .models import Supplier
from accounts.fields import ObjectIdField
from accounts.serializers import BaseMongoSerializer

class SupplierSerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    gst_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    pan_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Supplier
        fields = ('id', 'user', 'company_name', 'gst_number', 'pan_number', 'business_address', 'is_verified', 'certificate', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def validate_gst_number(self, value):
        return value.strip() if value and value.strip() else None

    def validate_pan_number(self, value):
        return value.strip() if value and value.strip() else None
