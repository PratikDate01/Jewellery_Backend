from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wishlist, WishlistItem
from .serializers import WishlistSerializer
from products.models import Product

class WishlistViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def get_wishlist(self):
        wishlist, created = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

    def list(self, request):
        wishlist = self.get_wishlist()
        serializer = self.get_serializer(wishlist)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        wishlist = self.get_wishlist()
        product_id = request.data.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
            wishlist_item, created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product
            )
            return Response({'status': 'product added to wishlist'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='remove')
    def remove(self, request):
        product_id = request.data.get('product_id')
        wishlist = self.get_wishlist()
        
        try:
            product = Product.objects.get(id=product_id)
            WishlistItem.objects.filter(wishlist=wishlist, product=product).delete()
            return Response({'status': 'product removed from wishlist'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
