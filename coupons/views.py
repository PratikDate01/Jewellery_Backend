from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Coupon
from .serializers import CouponSerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def validate(self, request):
        code = request.data.get('code')
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.is_valid():
                return Response({
                    'valid': True,
                    'discount_percentage': coupon.discount_percentage,
                    'code': coupon.code
                })
            else:
                return Response({'valid': False, 'error': 'Coupon is invalid or expired'}, status=status.HTTP_400_BAD_REQUEST)
        except Coupon.DoesNotExist:
            return Response({'valid': False, 'error': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)
