from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer
from accounts.fields import ObjectIdField

class CartItemSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_details', 'quantity', 'subtotal')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'product' in ret and ret['product']:
            ret['product'] = str(ret['product'])
        return ret

class CartSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    user = ObjectIdField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ('id', 'user', 'items', 'total_price', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'user' in ret and ret['user']:
            ret['user'] = str(ret['user'])
        return ret
