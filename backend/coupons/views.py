from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from auth.authentication import SessionJWtAuthentication
from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from users.permissions import IsAdmin


class CouponsViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    authentication_classes = [SessionJWtAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        coupon = serializer.save()
        coupon.refresh_from_db(fields=["created_at"])