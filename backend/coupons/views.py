from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from users.mixins import OwnerQuerysetMixin
from users.permissions import IsAdminOrReadOnly


class CouponsViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
