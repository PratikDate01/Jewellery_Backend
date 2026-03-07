from rest_framework import serializers
from .models import Coupon
from accounts.fields import ObjectIdField
from accounts.serializers import BaseMongoSerializer

class CouponSerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    class Meta:
        model = Coupon
        fields = '__all__'
