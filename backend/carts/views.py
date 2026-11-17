from rest_framework import viewsets

from carts.models import Carts
from carts.serializers import CartsSerializer
from users.mixins import OwnerQuerysetMixin
from users.permissions import IsAdminOrOwner


class CartsViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    queryset = Carts.objects.all()
    serializer_class = CartsSerializer
    permission_classes = [IsAdminOrOwner]
