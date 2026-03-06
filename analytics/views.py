from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from products.models import Product, SupplierProduct, PurchaseOrder, SupplierPayment
from orders.models import Order, OrderItem
from django.db import models
from django.db.models import Sum, Count, F
from wholesale.models import WholesaleProfile, NegotiationRequest
from suppliers.models import Supplier
from orders.serializers import OrderListSerializer
from products.serializers import ProductSerializer

User = get_user_model()

class AdminAnalyticsView(APIView):
    permission_classes = [permissions.IsAdminUser]

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

class WholesalerAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if not user or not hasattr(user, 'role'):
                 return Response({"detail": "User not fully authenticated."}, status=status.HTTP_401_UNAUTHORIZED)

            if user.role != 'WHOLESALER':
                return Response(
                    {"detail": "Access denied. Only wholesalers can access this endpoint."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            profile, created = WholesaleProfile.objects.get_or_create(user=user)

            total_orders = Order.objects.filter(user=user).count()
            active_negotiations = NegotiationRequest.objects.filter(wholesaler=profile, status='PENDING').count()
            total_spent = Order.objects.filter(user=user, payment_status='PAID').aggregate(Sum('net_amount'))['net_amount__sum'] or 0

            recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
            order_serializer = OrderListSerializer(recent_orders, many=True)

            data = {
                'stats': {
                    'total_orders': total_orders,
                    'active_negotiations': active_negotiations,
                    'total_spent': float(total_spent),
                    'company_name': profile.company_name,
                    'gst_number': profile.gst_number,
                    'is_verified': profile.is_verified
                },
                'recent_orders': order_serializer.data
            }
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SupplierAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            # Add safety check for user
            user = request.user
            if not user or not hasattr(user, 'role'):
                 return Response({"detail": "User not fully authenticated."}, status=status.HTTP_401_UNAUTHORIZED)

            if user.role != 'SUPPLIER':
                return Response(
                    {"detail": "Access denied. Only suppliers can access this endpoint."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Using SupplierProduct for supplier's own inventory
            supplier_products = SupplierProduct.objects.filter(supplier=user).prefetch_related('images')
            total_products = supplier_products.count()
            approved_products = supplier_products.filter(status='APPROVED').count()
            pending_products = supplier_products.filter(status='PENDING').count()
            
            # Real-world B2B stats: Based on Purchase Orders and Payments
            purchase_orders = PurchaseOrder.objects.filter(supplier=request.user)
            
            total_revenue = purchase_orders.aggregate(total=Sum('total_cost'))['total']
            if total_revenue is None: total_revenue = 0
            
            amount_paid = SupplierPayment.objects.filter(
                purchase_order__supplier=request.user
            ).aggregate(total=Sum('amount_paid'))['total']
            if amount_paid is None: amount_paid = 0
            
            pending_balance = float(total_revenue) - float(amount_paid)
            
            from products.serializers import SupplierProductSerializer
            product_serializer = SupplierProductSerializer(supplier_products, many=True)

            data = {
                'stats': {
                    'total_products': total_products,
                    'approved_products': approved_products,
                    'pending_products': pending_products,
                    'total_revenue': float(total_revenue),
                    'amount_paid': float(amount_paid),
                    'pending_balance': float(pending_balance),
                },
                'inventory': product_serializer.data
            }
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
