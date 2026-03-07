from rest_framework import serializers
from .models import Wishlist, WishlistItem
from products.serializers import ProductSerializer
from accounts.fields import ObjectIdField

class WishlistItemSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_details', 'added_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'product' in ret and ret['product']:
            ret['product'] = str(ret['product'])
        return ret

class WishlistSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'user', 'items', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'user' in ret and ret['user']:
            ret['user'] = str(ret['user'])
        return ret
