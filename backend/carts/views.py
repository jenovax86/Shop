from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from carts.models import Carts
from carts.serializers import CartsSerializer


class CartsViewSet(viewsets.ModelViewSet):
    serializer_class = CartsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Carts.objects.filter(user=self.request.user, deleted_at__isnull=True)

    def perform_create(self, serializer):
        user = serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
