from rest_framework import serializers
from .models import WholesaleProfile, NegotiationRequest
from products.serializers import ProductSerializer
from accounts.fields import ObjectIdField

class WholesaleProfileSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    class Meta:
        model = WholesaleProfile
        fields = ('id', 'user', 'company_name', 'gst_number', 'pan_number', 'business_address', 'is_verified', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

class NegotiationRequestSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    wholesaler_name = serializers.SerializerMethodField()

    class Meta:
        model = NegotiationRequest
        fields = ('id', 'wholesaler', 'wholesaler_name', 'product', 'product_name', 'product_details', 'quantity', 'offered_price', 'message', 'status', 'admin_response', 'created_at', 'updated_at')
        read_only_fields = ('id', 'wholesaler', 'created_at', 'updated_at')
    
    def get_wholesaler_name(self, obj):
        return obj.wholesaler.company_name if obj.wholesaler else "Unknown"
