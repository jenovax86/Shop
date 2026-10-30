from django.utils import timezone
from rest_framework import viewsets

from carts.models import Carts
from carts.serializers import CartsSerializer


class CartsViewSet(viewsets.ModelViewSet):
    queryset = Carts.objects.filter(deleted_at__isnull=True)
    serializer_class = CartsSerializer


    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])