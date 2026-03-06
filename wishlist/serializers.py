from rest_framework import serializers
from .models import Wishlist, WishlistItem
from products.serializers import ProductSerializer

class WishlistItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_details', 'added_at')

class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'user', 'items', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
