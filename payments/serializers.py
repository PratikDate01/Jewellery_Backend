from rest_framework import serializers
from .models import Payment
from accounts.fields import ObjectIdField

class PaymentSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    class Meta:
        model = Payment
        fields = ('id', 'user', 'order', 'transaction_id', 'payment_method', 'payment_details', 'amount', 'status', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'status', 'created_at', 'updated_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        for field in ['user', 'order']:
            if field in ret and ret[field]:
                ret[field] = str(ret[field])
        return ret
