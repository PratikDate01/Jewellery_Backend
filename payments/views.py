import uuid
import time
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer
from orders.models import Order
from django.db import transaction

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def process_payment(self, request):
        order_id = request.data.get('order_id')
        payment_method = request.data.get('payment_method', 'CARD')
        payment_details = request.data.get('payment_details', {})

        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status == 'PAID':
            return Response({'error': 'Order already paid'}, status=status.HTTP_400_BAD_REQUEST)

        # Simulate a slight delay for "processing"
        # time.sleep(1) # Using time.sleep might block the thread in some dev setups, 
        # but it's fine for simulating a "professional" feel in a demo.

        # In a real "own" system, we'd integrate with a bank API or Stripe here.
        # For this request, we'll simulate the "Gateway" logic.
        
        transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        with transaction.atomic():
            # Create or update payment record
            payment, created = Payment.objects.update_or_create(
                order=order,
                defaults={
                    'user': self.request.user,
                    'transaction_id': transaction_id,
                    'payment_method': payment_method,
                    'payment_details': payment_details,
                    'amount': order.net_amount,
                    'status': 'SUCCESS'
                }
            )

            # Update Order
            order.payment_status = 'PAID'
            order.payment_method = payment_method
            order.status = 'CONFIRMED'
            order.save()

        return Response({
            'status': 'Payment successful',
            'transaction_id': transaction_id,
            'amount': order.net_amount,
            'order_id': order.id
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def fail_payment(self, request):
        """Simulate a failed payment for testing"""
        order_id = request.data.get('order_id')
        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        transaction_id = f"FAIL-{uuid.uuid4().hex[:12].upper()}"
        
        Payment.objects.create(
            order=order,
            user=self.request.user,
            transaction_id=transaction_id,
            amount=order.net_amount,
            status='FAILED'
        )
        
        order.payment_status = 'FAILED'
        order.save()

        return Response({'status': 'Payment failed', 'transaction_id': transaction_id}, status=status.HTTP_400_BAD_REQUEST)
