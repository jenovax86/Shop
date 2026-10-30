from django.utils import timezone
from rest_framework import viewsets

from addresses.models import Address
from addresses.serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.filter(deleted_at__isnull=True)
    serializer_class = AddressSerializer

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
