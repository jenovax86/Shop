from rest_framework import viewsets

from addresses.models import Address
from addresses.serializers import AddressSerializer
from core.pagination import JSONAPIPagination
from users.mixins import OwnerQuerysetMixin
from users.permissions import IsAdminOrOwner


class AddressPagination(JSONAPIPagination):
    page_size = 10
    ordering = '-id'


class AddressViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    pagination_class = AddressPagination
    permission_classes = [IsAdminOrOwner]
