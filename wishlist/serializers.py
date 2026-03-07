from rest_framework import serializers
from .models import Wishlist, WishlistItem
from products.serializers import ProductSerializer
from accounts.fields import ObjectIdField
from accounts.serializers import BaseMongoSerializer

class WishlistItemSerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_details', 'added_at')


class WishlistSerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'user', 'items', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
