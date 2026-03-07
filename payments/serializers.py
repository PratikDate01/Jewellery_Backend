from rest_framework import serializers
from .models import Payment
from accounts.fields import ObjectIdField
from accounts.serializers import BaseMongoSerializer

class PaymentSerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    class Meta:
        model = Payment
        fields = ('id', 'user', 'order', 'transaction_id', 'payment_method', 'payment_details', 'amount', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'status', 'created_at', 'updated_at')
