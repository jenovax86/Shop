from django.db import transaction
from rest_framework import viewsets

from orders.models import Order
from orders.serializers import AdminOrderSerializer, OrderSerializer
from orders.services.order import create_order
from users.mixins import OwnerQuerysetMixin
from users.permissions import IsAdminOrOwner, is_admin


class OrderViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    """Users manage only their own orders; user, state, price and discounted_price are protected. Administrators manage all orders and may change ownership, pricing, state and deleted_at."""
    queryset = Order.objects.all()
    permission_classes = [IsAdminOrOwner]

    def get_serializer_class(self):
        return AdminOrderSerializer if getattr(self, "swagger_fake_view", False) or is_admin(
            self.request.user) else OrderSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        if is_admin(self.request.user):
            serializer.save(user=serializer.validated_data.get("user", self.request.user))
        else:
            create_order(self.request.user, serializer)
