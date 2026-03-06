from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'user', 'order', 'transaction_id', 'payment_method', 'payment_details', 'amount', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'status', 'created_at', 'updated_at')
