from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.response import Response

from carts.models import CartItems
from coupons.models import Coupon
from orders.models import Order, OrderProduct
from orders.serializers import AdminOrderSerializer, OrderSerializer
from users.mixins import OwnerQuerysetMixin
from users.permissions import IsAdminOrOwner, is_admin


class OrderViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAdminOrOwner]

    def get_serializer_class(self):
        return AdminOrderSerializer if getattr(self, "swagger_fake_view", False) or is_admin(
            self.request.user) else OrderSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        if is_admin(user):
            serializer.save(user=serializer.validated_data.get("user", user))
        else:
            data = serializer.validated_data
            cart = data.pop("cart")
            coupon = data.get("coupon")
            total_price = Decimal("0.00")
            discounted_product_prices = Decimal("0.00")
            cart_items = list(
                CartItems.objects.filter(
                    cart=cart,
                    deleted_at__isnull=True,
                ).select_related("product")
            )

            if not cart_items:
                raise ValidationError("Cart is empty.")

            if coupon is not None:
                if (
                        coupon.user_id != user.pk
                        or coupon.expires_at <= timezone.now()
                ):
                    raise ValidationError("Invalid or expired coupon.")

            order_products_data = []

            for item in cart_items:
                product = item.product

                original_price = product.price
                discount_amount = (
                    product.discount_amount
                    if product.discount_amount is not None
                    else Decimal("0.00")
                )

                unit_price = original_price - discount_amount

                total_price += original_price * item.quantity

                discounted_product_prices += unit_price * item.quantity

                order_products_data.append({
                    "product": product,
                    "quantity": item.quantity,
                    "original_price": original_price,
                    "price": unit_price,
                    "size": item.size,
                    "color": item.color,
                })

            discounted_price = discounted_product_prices

            if coupon is not None:
                coupon_discount = (
                        discounted_product_prices
                        * coupon.percentage
                        / Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                discounted_price -= coupon_discount

            order = serializer.save(
                user=user,
                coupon=coupon,
                price=total_price,
                discounted_price=discounted_price,
                state=Order.State.PENDING,
            )

            OrderProduct.objects.bulk_create([
                OrderProduct(order=order, **item_data)
                for item_data in order_products_data
            ])

            CartItems.objects.filter(
                cart=cart,
                deleted_at__isnull=True,
            ).update(deleted_at=timezone.now())

    def perform_destroy(self, request):
        raise MethodNotAllowed("DELETE", "Orders cannot be deleted.")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk):
        order = self.get_object()
        if order.state != Order.State.PENDING:
            raise ValidationError(
                "This order cannot be cancelled."
            )
        order.state = Order.State.CANCELLED
        order.save(update_fields=["state"])
        return Response(
            {"detail": "Order cancelled successfully."},
            status=status.HTTP_200_OK,
        )
