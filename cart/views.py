from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product

class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        user = request.user
        if not user or user.is_anonymous:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        cart, created = Cart.objects.get_or_create(user=user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if not product.is_available_for_sale:
            return Response({'error': 'Product is currently not available for sale'}, status=status.HTTP_400_BAD_REQUEST)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        current_cart_qty = cart_item.quantity if cart_item else 0
        total_requested_qty = current_cart_qty + quantity

        if total_requested_qty > product.stock_quantity:
            return Response({
                'error': f'Cannot add more items than available stock. Available: {product.stock_quantity}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if cart_item:
            cart_item.quantity = total_requested_qty
            cart_item.save()
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)
            
        return Response({'status': 'Item added to cart'}, status=status.HTTP_200_OK)

class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        product = serializer.validated_data.get('product')
        quantity = serializer.validated_data.get('quantity', 1)

        if not product.is_available_for_sale:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Product is currently not available for sale")

        # Check if item already exists in cart
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        current_cart_qty = cart_item.quantity if cart_item else 0
        total_requested_qty = current_cart_qty + quantity

        if total_requested_qty > product.stock_quantity:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Insufficient stock. Available: {product.stock_quantity}")

        if cart_item:
            cart_item.quantity = total_requested_qty
            cart_item.save()
            serializer.instance = cart_item
        else:
            serializer.save(cart=cart)

    def perform_update(self, serializer):
        product = serializer.instance.product
        quantity = serializer.validated_data.get('quantity', serializer.instance.quantity)

        if quantity > product.stock_quantity:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(f"Insufficient stock. Available: {product.stock_quantity}")
        
        serializer.save()
