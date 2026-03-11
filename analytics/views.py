from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from accounts.permissions import IsAdmin
from django.contrib.auth import get_user_model
from products.models import Product, SupplierProduct, PurchaseOrder, SupplierPayment
from orders.models import Order, OrderItem
from django.db import models
from django.db.models import Sum, Count, Q
from suppliers.models import Supplier
from orders.serializers import OrderListSerializer
from products.serializers import ProductSerializer, SupplierProductSerializer
from wishlist.models import Wishlist
from wishlist.serializers import WishlistSerializer

User = get_user_model()

class AdminAnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            total_users = User.objects.count()
            total_customers = User.objects.filter(role='CUSTOMER').count()
            total_suppliers = User.objects.filter(role='SUPPLIER').count()
            
            total_products = Product.objects.count()
            approved_products = Product.objects.filter(is_approved=True).count()
            
            total_orders = Order.objects.count()
            total_revenue = Order.objects.filter(payment_status='PAID').aggregate(Sum('net_amount'))['net_amount__sum'] or 0
            
            # B2B Financial Tracking: Payments to Suppliers
            total_supplier_payments = SupplierPayment.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            
            recent_orders = Order.objects.order_by('-created_at')[:5]
            order_serializer = OrderListSerializer(recent_orders, many=True)

            low_stock_products = Product.objects.filter(stock_quantity__lte=5)[:4]
            product_serializer = ProductSerializer(low_stock_products, many=True)

            data = {
                'stats': {
                    'total_users': total_users,
                    'total_customers': total_customers,
                    'total_suppliers': total_suppliers,
                    'total_products': total_products,
                    'approved_products': approved_products,
                    'total_orders': total_orders,
                    'total_revenue': float(total_revenue),
                    'total_supplier_payments': float(total_supplier_payments),
                },
                'recent_orders': order_serializer.data,
                'low_stock_products': product_serializer.data
            }
            
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SupplierAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if user.role != 'SUPPLIER':
                return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            
            products = SupplierProduct.objects.filter(supplier=user)
            pos = PurchaseOrder.objects.filter(supplier=user)
            
            data = {
                'stats': {
                    'total_products': products.count(),
                    'approved_products': products.filter(status='APPROVED').count(),
                    'total_revenue': float(pos.aggregate(Sum('total_cost'))['total_cost__sum'] or 0),
                },
                'inventory': SupplierProductSerializer(products[:10], many=True).data
            }
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UnifiedDashboardView(APIView):
    """
    Unified endpoint to fetch all dashboard data for the current user's role.
    Drastically reduces API calls from the frontend.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        role = getattr(user, 'role', None)

        try:
            if role == 'ADMIN':
                return self._get_admin_data(request)
            elif role == 'SUPPLIER':
                return self._get_supplier_data(request)
            elif role == 'CUSTOMER':
                return self._get_customer_data(request)
            else:
                return Response({"error": "Unknown role"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_admin_data(self, request):
        total_users = User.objects.count()
        total_revenue = Order.objects.filter(payment_status='PAID').aggregate(Sum('net_amount'))['net_amount__sum'] or 0
        recent_orders = Order.objects.order_by('-created_at')[:5]
        low_stock = Product.objects.filter(stock_quantity__lte=5)[:5]
        
        return Response({
            'role': 'ADMIN',
            'stats': {
                'total_users': total_users,
                'total_revenue': float(total_revenue),
                'total_products': Product.objects.count(),
                'pending_approvals': SupplierProduct.objects.filter(status='PENDING').count()
            },
            'recent_orders': OrderListSerializer(recent_orders, many=True).data,
            'low_stock': ProductSerializer(low_stock, many=True).data
        })

    def _get_supplier_data(self, request):
        user = request.user
        supplier_products = SupplierProduct.objects.filter(supplier=user)
        purchase_orders = PurchaseOrder.objects.filter(supplier=user)
        
        total_rev = purchase_orders.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
        paid_amt = SupplierPayment.objects.filter(purchase_order__supplier=user).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        return Response({
            'role': 'SUPPLIER',
            'stats': {
                'total_products': supplier_products.count(),
                'approved_products': supplier_products.filter(status='APPROVED').count(),
                'total_earnings': float(total_rev),
                'total_revenue': float(total_rev),
                'pending_balance': float(total_rev) - float(paid_amt)
            },
            'inventory': SupplierProductSerializer(supplier_products[:50], many=True).data,
            'recent_orders': [] # Suppliers might need recent POs here
        })

    def _get_customer_data(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)
        wishlist, _ = Wishlist.objects.get_or_create(user=user)
        
        return Response({
            'role': 'CUSTOMER',
            'stats': {
                'total_orders': orders.count(),
                'total_spent': float(orders.filter(payment_status='PAID').aggregate(Sum('net_amount'))['net_amount__sum'] or 0),
                'wishlist_count': wishlist.items.count()
            },
            'recent_orders': OrderListSerializer(orders.order_by('-created_at')[:5], many=True).data,
            'wishlist': WishlistSerializer(wishlist).data
        })
