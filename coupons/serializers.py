from rest_framework import serializers
from .models import Coupon
from accounts.fields import ObjectIdField

class CouponSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    class Meta:
        model = Coupon
        fields = '__all__'
