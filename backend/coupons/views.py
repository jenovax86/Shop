from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from users.permissions import IsAdminOrReadOnly


class CouponsViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        coupon = serializer.save()
        coupon.refresh_from_db(fields=["created_at"])