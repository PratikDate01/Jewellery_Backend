from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from .models import WholesaleProfile, NegotiationRequest
from .serializers import WholesaleProfileSerializer, NegotiationRequestSerializer
from accounts.permissions import IsAdmin
from orders.models import Order
from django.db.models import Sum
import uuid

class WholesaleProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WholesaleProfileSerializer

    def get_queryset(self):
        return WholesaleProfile.objects.filter(user=self.request.user)

    def get_object(self):
        obj, created = WholesaleProfile.objects.get_or_create(user=self.request.user)
        return obj

    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        profile, created = WholesaleProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def negotiations(self, request):
        profile = self.get_object()
        negotiations = NegotiationRequest.objects.filter(wholesaler=profile).order_by('-created_at')
        serializer = NegotiationRequestSerializer(negotiations, many=True)
        return Response(serializer.data)

class NegotiationRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NegotiationRequestSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != 'WHOLESALER':
            return Response({"error": "Only wholesalers can request negotiations"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            profile = request.user.wholesale_profile
            if not profile.is_verified:
                return Response({"error": "Your wholesale account is pending verification by admin."}, status=status.HTTP_403_FORBIDDEN)
        except WholesaleProfile.DoesNotExist:
             return Response({"error": "Please complete your wholesale profile before requesting negotiations."}, status=status.HTTP_400_BAD_REQUEST)
             
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return NegotiationRequest.objects.none()
        if user.role == 'WHOLESALER':
            try:
                wholesaler_profile = user.wholesale_profile
            except WholesaleProfile.DoesNotExist:
                return NegotiationRequest.objects.none()
            return NegotiationRequest.objects.filter(wholesaler=wholesaler_profile).order_by('-created_at')
        elif user.role == 'ADMIN':
            return NegotiationRequest.objects.all().order_by('-created_at')
        return NegotiationRequest.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == 'WHOLESALER':
            try:
                wholesaler_profile = self.request.user.wholesale_profile
            except WholesaleProfile.DoesNotExist:
                wholesaler_profile = WholesaleProfile.objects.create(
                    user=self.request.user,
                    company_name=self.request.user.name or self.request.user.email,
                    gst_number=f"GST{uuid.uuid4().hex[:12].upper()}",
                    pan_number=f"PAN{uuid.uuid4().hex[:10].upper()}",
                    business_address="To be updated"
                )
            serializer.save(wholesaler=wholesaler_profile)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def accept(self, request, pk=None):
        negotiation = self.get_object()
        negotiation.status = 'ACCEPTED'
        negotiation.admin_response = request.data.get('response', 'Negotiation accepted.')
        negotiation.save()
        return Response({'status': 'accepted'})

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def reject(self, request, pk=None):
        negotiation = self.get_object()
        negotiation.status = 'REJECTED'
        negotiation.admin_response = request.data.get('response', 'Negotiation rejected.')
        negotiation.save()
        return Response({'status': 'rejected'})
