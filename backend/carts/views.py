from rest_framework import viewsets, status
from rest_framework.response import Response

from carts.models import Carts, CartItems
from carts.serializers import CartsSerializer, CartItemsSerializer
from users.mixins import OwnerQuerysetMixin
from users.permissions import IsAdminOrOwner


class CartsViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    queryset = Carts.objects.all()
    serializer_class = CartsSerializer
    permission_classes = [IsAdminOrOwner]


class CartItemsViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    queryset = CartItems.objects.all()
    serializer_class = CartItemsSerializer
    permission_classes = [IsAdminOrOwner]

    def get_queryset(self):
        return CartItems.objects.filter(cart__user=self.request.user, deleted_at__isnull=True)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cart = data['cart']
        item, created = CartItems.objects.get_or_create(cart=cart, product=data['product'], size=data['size'],
                                                        color=data['color'], defaults={"quantity": data['quantity']},
                                                        deleted_at__isnull=True)
        if not created:
            CartItems.objects.filter(pk=item.pk).update(quantity=item.quantity + data['quantity'])
            item.refresh_from_db()

        response_serializer = self.get_serializer(item)
        return Response(
            response_serializer.data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )
