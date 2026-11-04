from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from orders.models import Order
from orders.serializers import OrderSerializer
from orders.services.order import create_order



class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.filter(deleted_at__isnull=True)
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        create_order(user, serializer)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])
